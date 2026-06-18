# Serveur VPN d’entreprise avec portail d’administration
## Infrastructure Documentation

**Project Type:** Cybersecurity Capstone Project  
**Domain:** `hightech.local`  
**VPN Solution:** OpenVPN  
**Directory Service:** Active Directory Domain Services (AD DS)  
**Operating Systems:** Windows Server 2022, Ubuntu 24.04 LTS  
**Application Stack:** React, FastAPI, PostgreSQL  
**Authentication Sources:** Active Directory + Local Application Accounts  
**Authorization Model:** RBAC + Active Directory Group Membership

---

# 1. Project Overview

This project implements a secure remote access management platform integrating:

- Active Directory
- OpenVPN
- Ubuntu Linux
- Windows Server
- PostgreSQL
- FastAPI
- React

The objective is to centralize VPN access requests, automate approval workflows, and leverage Active Directory for authentication and authorization.

---

# 2. Infrastructure Architecture

```text
                           +----------------+
                           | VPN Client     |
                           | OpenVPN Client |
                           +--------+-------+
                                    |
                                    |
                                    v
+--------------------------------------------------------+
| Ubuntu 24.04 VPN Server                                |
|--------------------------------------------------------|
| OpenVPN Server                                         |
| PAM Authentication                                     |
| SSSD                                                   |
| Active Directory Integration                           |
| FastAPI Backend                                        |
| PostgreSQL                                             |
+-------------------+------------------------------------+
                    |
                    |
                    v
+--------------------------------------------------------+
| Windows Server 2022                                    |
|--------------------------------------------------------|
| Active Directory Domain Services                       |
| DNS Server                                             |
| Domain Controller                                      |
| Group Management                                       |
+--------------------------------------------------------+

                    |
                    |
                    v

+--------------------------------------------------------+
| React Frontend                                         |
|--------------------------------------------------------|
| VPN Request Portal                                     |
| Administration Portal                                 |
| Security Dashboard                                     |
+--------------------------------------------------------+
```

---

# 3. Network Architecture

## VMware Network

### Domain Controller

| Parameter | Value |
|------------|--------|
| Hostname | DC01 |
| Domain | hightech.local |
| IP Address | 192.168.182.130 |
| Subnet Mask | 255.255.255.0 |
| Gateway | 192.168.182.2 |
| DNS | 192.168.182.130 |

---

### Ubuntu VPN/Application Server

| Parameter | Value |
|------------|--------|
| Hostname | ubuntu2404 |
| IP Address | 192.168.182.129 |
| Subnet Mask | 255.255.255.0 |
| Gateway | 192.168.182.2 |
| DNS | 192.168.182.130 |

---

### VPN Network

| Parameter | Value |
|------------|--------|
| VPN Subnet | 10.8.0.0/24 |
| VPN Gateway | 10.8.0.1 |
| Client Pool | 10.8.0.2 - 10.8.0.254 |

---

# 4. Active Directory Infrastructure

## Domain Configuration

| Setting | Value |
|-----------|--------|
| Domain Name | hightech.local |
| NetBIOS Name | HIGHTECH |
| Domain Controller | DC01 |
| Functional Level | Windows Server 2022 |

---

## Organizational Units

```text
hightech.local
│
├── Users
│
├── Groups
│
├── Computers
│
└── Service Accounts
```

---

## Security Groups

### VPN_Users

Purpose:

Users authorized to connect through OpenVPN.

```text
VPN_Users
```

---

## Service Accounts

### VPN Application Service Account

```text
svc_vpn_app@hightech.local
```

Purpose:

- LDAP Queries
- Group Management
- VPN Approval Workflow

Required Permissions:

- Read AD Users
- Read Groups
- Add Members to VPN_Users
- Remove Members from VPN_Users

---

# 5. Ubuntu Domain Integration

## Components

Installed packages:

```bash
sudo apt update
sudo apt install realmd sssd sssd-tools adcli oddjob oddjob-mkhomedir packagekit krb5-user samba-common-bin ldap-utils -y
```

---

## Domain Join

```bash
sudo realm join hightech.local -U Administrator
```

Verification:

```bash
realm list
```

---

## SSSD Configuration

Location:

```text
/etc/sssd/sssd.conf
```

Purpose:

- Active Directory Authentication
- Group Resolution
- Authorization

---

## User Verification

```bash
id user@hightech.local
```

---

## Group Verification

```bash
getent group "vpn users@hightech.local"
```

---

# 6. OpenVPN Infrastructure

## Installed Components

```bash
sudo apt install openvpn easy-rsa -y
```

---

## Authentication Method

Authentication relies on:

```text
OpenVPN
    ↓
PAM
    ↓
SSSD
    ↓
Active Directory
```

---

## VPN Authorization

Users must belong to:

```text
VPN_Users
```

Active Directory group.

---

## OpenVPN Server Configuration

Location:

```text
/etc/openvpn/server/server.conf
```

Important parameters:

```conf
port 1194
proto udp
dev tun

topology subnet

server 10.8.0.0 255.255.255.0

push "redirect-gateway def1"
push "dhcp-option DNS 8.8.8.8"

plugin /usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so openvpn-ad

username-as-common-name
client-cert-not-required
verify-client-cert none

cipher AES-256-GCM
auth SHA256

persist-key
persist-tun

keepalive 10 120
```

---

## PAM Configuration

Location:

```text
/etc/pam.d/openvpn-ad
```

Content:

```text
auth required pam_sss.so
account required pam_sss.so
```

---

# 7. PostgreSQL Infrastructure

## Purpose

Stores:

- Application Users
- Roles
- Permissions
- VPN Requests
- Audit Logs

---

## Installation

```bash
sudo apt install postgresql postgresql-contrib -y
```

---

## Database

```text
vpn_portal
```

---

# 8. Web Application Architecture

## Backend

Technology:

- FastAPI
- SQLAlchemy
- Alembic
- LDAP3
- JWT Authentication

---

## Frontend

Technology:

- React
- Vite
- TailwindCSS
- Axios

---

# 9. Authentication Architecture

## VPN Users

Authentication Source:

```text
Active Directory
```

Credentials:

```text
username@hightech.local
password
```

Passwords are never stored.

Authentication method:

LDAP Bind.

---

## Administrative Users

Authentication Source:

```text
PostgreSQL
```

Credentials:

```text
username
password
```

Passwords stored using:

```text
bcrypt
```

Authentication:

```text
JWT
```

---

# 10. Authorization Model

## RBAC

### ADMIN

Permissions:

- Manage Users
- Manage Roles
- Manage Permissions
- View Logs
- View Reports
- Manage Analysts

---

### SECURITY_ANALYST

Permissions:

- Review Requests
- Approve Requests
- Reject Requests
- View Logs
- View VPN Users

---

### AUDITOR

Permissions:

- Read Logs
- Read Reports
- Read Requests

No modification rights.

---

# 11. VPN Request Workflow

## Step 1

User submits:

```text
username@hightech.local
password
```

---

## Step 2

FastAPI performs:

```text
LDAP Bind
```

against:

```text
hightech.local
```

---

## Step 3

If successful:

```text
Request Status = PENDING
```

---

## Step 4

Security Analyst reviews request.

---

## Step 5

Analyst chooses:

```text
APPROVE
```

or

```text
REJECT
```

---

## Step 6

If approved:

```text
FastAPI
    ↓
LDAP Service Account
    ↓
Active Directory
    ↓
VPN_Users Group
```

User gains VPN access immediately.

---

# 12. Database Schema

## application_users

```sql
id
username
password_hash
role_id
is_active
created_at
```

---

## roles

```sql
id
name
```

---

## permissions

```sql
id
name
```

---

## role_permissions

```sql
role_id
permission_id
```

---

## vpn_requests

```sql
id
ad_username
display_name
department
status
requested_at
reviewed_at
reviewed_by
rejection_reason
```

---

## audit_logs

```sql
id
actor
action
target
source_ip
timestamp
```

---

# 13. Audit Logging

Every security-sensitive action is logged.

Examples:

```text
USER_LOGIN
USER_LOGOUT

REQUEST_CREATED
REQUEST_APPROVED
REQUEST_REJECTED

AD_GROUP_MEMBER_ADDED
AD_GROUP_MEMBER_REMOVED

ROLE_CREATED
ROLE_UPDATED

PERMISSION_CREATED
PERMISSION_UPDATED
```

---

# 14. Security Controls

## Password Security

Application Users:

```text
bcrypt
```

---

## VPN Encryption

```text
TLS 1.3
AES-256-GCM
```

---

## Access Control

```text
RBAC
```

for application users.

```text
AD Group Membership
```

for VPN authorization.

---

## Auditability

Every action recorded.

---

## Principle of Least Privilege

Dedicated service account.

No use of Domain Administrator account.

---

# 15. Future Enhancements

## MFA

Potential integration:

- TOTP
- Microsoft Authenticator
- Google Authenticator

---

## Access Expiration

Automatic removal from:

```text
VPN_Users
```

after defined period.

---

## VPN Session Monitoring

Display:

- Connected Users
- Assigned IP
- Session Duration
- Bandwidth Usage

---

## SIEM Integration

Potential integrations:

- Wazuh
- ELK Stack
- Splunk

---

# 16. Conclusion

This infrastructure provides:

- Centralized Identity Management
- Secure VPN Access
- Active Directory Integration
- Role-Based Administration
- Access Governance Workflow
- Audit Logging
- Enterprise-Oriented Security Controls

The platform demonstrates the implementation of Authentication, Authorization, and Accounting (AAA) principles within a realistic enterprise cybersecurity environment.
