from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql://vpnapp:vpnapp_pass@localhost:5432/vpnapp"

    # LDAP / Active Directory
    LDAP_SERVER: str = "ldap://192.168.182.130"
    LDAP_PORT: int = 389
    LDAP_BASE_DN: str = "DC=hightech,DC=local"
    LDAP_DOMAIN: str = "hightech.local"
    LDAP_SERVICE_ACCOUNT: str = "vpnsvc@hightech.local"
    LDAP_SERVICE_PASSWORD: str = ""
    LDAP_VPN_GROUP_DN: str = "CN=VPN_Users,CN=Users,DC=hightech,DC=local"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Monitoring / log collection
    OPENVPN_STATUS_LOG: str = "/var/log/openvpn-status.log"
    AUTH_LOG: str = "/var/log/auth.log"

    # Alert detection thresholds
    BRUTE_FORCE_THRESHOLD: int = 4
    BRUTE_FORCE_WINDOW_SECONDS: int = 120
    SPRAY_THRESHOLD: int = 4
    SPRAY_MIN_USERNAMES: int = 3
    SPRAY_WINDOW_SECONDS: int = 120

    # UFW enforcement
    UFW_BIN: str = "/usr/sbin/ufw"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()