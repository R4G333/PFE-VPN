"""
Active Directory integration via ldap3 (LDAPS-secured).
All communication uses LDAPS (port 636) with TLS.

Functions:
  - authenticate_user()          : validate AD credentials via LDAPS bind
  - get_user_display_name()      : fetch displayName attribute
  - add_user_to_vpn_group()      : add user DN to VPN_Users group
  - remove_user_from_vpn_group() : remove user DN from VPN_Users group
  - get_vpn_group_members()      : list current VPN_Users group members
"""
import logging
import ssl
from dataclasses import dataclass

from ldap3 import (
    ALL,
    BASE,
    Connection,
    MODIFY_ADD,
    MODIFY_DELETE,
    Server,
    SUBTREE,
    Tls,
)
from ldap3.core.exceptions import LDAPException

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ─────────────────────────────────────────────────────────────
# TLS / SERVER CONFIG
# ─────────────────────────────────────────────────────────────

def _get_tls() -> Tls:
    """
    LDAPS TLS configuration.
    If AD has a valid (trusted) certificate, switch validate to CERT_REQUIRED
    and supply ca_certs_file pointing to the CA bundle.
    """
    return Tls(
        validate=ssl.CERT_NONE,  # change to CERT_REQUIRED in production
        version=ssl.PROTOCOL_TLS_CLIENT,
    )


def _get_server() -> Server:
    return Server(
        settings.LDAP_SERVER,
        port=settings.LDAP_PORT,                 # LDAPS only
        use_ssl=True,
        get_info=ALL,
        tls=_get_tls(),
    )


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _service_connection() -> Connection:
    """Reusable service account connection (read/write)."""
    return Connection(
        _get_server(),
        user=settings.LDAP_SERVICE_ACCOUNT,
        password=settings.LDAP_SERVICE_PASSWORD,
        auto_bind=True,
    )


def _user_dn_from_samaccount(sam_account: str) -> str | None:
    """
    Resolve sAMAccountName or UPN to Distinguished Name.
    """
    username = sam_account.split("@")[0]
    try:
        conn = _service_connection()
        conn.search(
            search_base=settings.LDAP_BASE_DN,
            search_filter=f"(sAMAccountName={username})",
            search_scope=SUBTREE,
            attributes=["distinguishedName"],
        )
        if conn.entries:
            return str(conn.entries[0].distinguishedName)
        return None
    except LDAPException as exc:
        logger.error("DN lookup failed for %s: %s", username, exc)
        return None


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

@dataclass
class LdapUserInfo:
    dn: str
    display_name: str
    sam_account: str


@dataclass
class VpnGroupMember:
    sam_account: str
    display_name: str
    dn: str


def authenticate_user(upn: str, password: str) -> bool:
    """
    Authenticate user using LDAPS simple bind.
    """
    try:
        conn = Connection(
            _get_server(),
            user=upn,
            password=password,
            auto_bind=True,
        )
        conn.unbind()
        return True
    except LDAPException as exc:
        logger.warning("Authentication failed for %s: %s", upn, exc)
        return False


def get_user_display_name(upn: str) -> str:
    """
    Fetch displayName from AD.
    """
    username = upn.split("@")[0]
    try:
        conn = _service_connection()
        conn.search(
            search_base=settings.LDAP_BASE_DN,
            search_filter=f"(sAMAccountName={username})",
            search_scope=SUBTREE,
            attributes=["displayName", "cn"],
        )
        if not conn.entries:
            return upn
        entry = conn.entries[0]
        if getattr(entry, "displayName", None):
            return str(entry.displayName)
        if getattr(entry, "cn", None):
            return str(entry.cn)
        return upn
    except LDAPException as exc:
        logger.error("Display name lookup failed for %s: %s", upn, exc)
        return upn


def add_user_to_vpn_group(upn: str) -> bool:
    """
    Add user to VPN_Users group.
    """
    user_dn = _user_dn_from_samaccount(upn)
    if not user_dn:
        logger.error("User DN not found for %s", upn)
        return False
    try:
        conn = _service_connection()
        conn.modify(
            settings.LDAP_VPN_GROUP_DN,
            {"member": [(MODIFY_ADD, [user_dn])]},
        )
        result_code = conn.result["result"]
        if result_code == 0:
            logger.info("Added %s to VPN_Users", upn)
            return True
        if result_code == 68:
            logger.info("User %s already in VPN_Users", upn)
            return True
        logger.error(
            "Failed to add %s to VPN_Users: %s",
            upn,
            conn.result.get("description"),
        )
        return False
    except LDAPException as exc:
        logger.error("Group update failed for %s: %s", upn, exc)
        return False


def remove_user_from_vpn_group(upn: str) -> bool:
    """
    Remove user from VPN_Users group (revoke VPN access).
    Returns True on success, or if the user was already not a member.
    """
    user_dn = _user_dn_from_samaccount(upn)
    if not user_dn:
        logger.error("User DN not found for %s", upn)
        return False
    try:
        conn = _service_connection()
        conn.modify(
            settings.LDAP_VPN_GROUP_DN,
            {"member": [(MODIFY_DELETE, [user_dn])]},
        )
        result_code = conn.result["result"]
        if result_code == 0:
            logger.info("Removed %s from VPN_Users", upn)
            return True
        # 16 = noSuchAttribute -> user wasn't a member; treat as success
        if result_code == 16:
            logger.info("User %s was not a member of VPN_Users", upn)
            return True
        logger.error(
            "Failed to remove %s from VPN_Users: %s",
            upn,
            conn.result.get("description"),
        )
        return False
    except LDAPException as exc:
        logger.error("Group update failed for %s: %s", upn, exc)
        return False


def get_vpn_group_members() -> list[VpnGroupMember]:
    """
    List current members of the VPN_Users AD group.
    """
    try:
        conn = _service_connection()
        conn.search(
            search_base=settings.LDAP_VPN_GROUP_DN,
            search_filter="(objectClass=group)",
            search_scope=BASE,
            attributes=["member"],
        )
        if not conn.entries:
            return []

        member_dns = list(conn.entries[0].member.values) if conn.entries[0].member else []

        members: list[VpnGroupMember] = []
        for dn in member_dns:
            conn.search(
                search_base=dn,
                search_filter="(objectClass=user)",
                search_scope=BASE,
                attributes=["sAMAccountName", "displayName", "cn"],
            )
            if not conn.entries:
                continue
            entry = conn.entries[0]
            sam = str(entry.sAMAccountName) if getattr(entry, "sAMAccountName", None) else ""
            display = (
                str(entry.displayName)
                if getattr(entry, "displayName", None)
                else (str(entry.cn) if getattr(entry, "cn", None) else sam)
            )
            members.append(VpnGroupMember(sam_account=sam, display_name=display, dn=dn))

        return members
    except LDAPException as exc:
        logger.error("Failed to list VPN_Users group members: %s", exc)
        return []
