# Sentinel VAC Backend

Backend API for the Sentinel VAC (VPN Access Control) platform.

Sentinel VAC is a Secure Remote Access Management System designed to automate VPN access governance using Active Directory authentication, OpenVPN integration, Role-Based Access Control (RBAC), security monitoring, and audit logging.

---

## Features

### VPN Access Governance

- Active Directory credential validation (LDAPS)
- VPN access request workflow
- Request approval/rejection process
- Automatic management of AD `VPN_Users` group membership
- Access revocation support

### Authentication & Authorization

- JWT Authentication
- Refresh Tokens
- Role-Based Access Control (RBAC)
- Bcrypt password hashing
- Account activation/deactivation

### Security Monitoring

- OpenVPN session monitoring
- Authentication event collection
- Brute-force detection
- Password spraying detection
- Alert management

### Device Blocking

- UFW integration
- IP blocking/unblocking
- Firewall enforcement queue

### Auditing

- Immutable audit trail
- Administrative activity tracking
- Security event logging

---

# Architecture

```text
Client
  │
  ▼
FastAPI Routers
  │
  ▼
Services Layer
  │
  ▼
Repositories
  │
  ▼
PostgreSQL

       │
       ▼
Active Directory (LDAPS)

       │
       ▼
OpenVPN Monitoring Scripts
```

The application follows a strict:

```text
Router → Service → Repository
```

architecture.

---

# Tech Stack

| Component | Technology |
|------------|------------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Authentication | JWT |
| Password Hashing | bcrypt |
| Directory Services | ldap3 |
| Database | PostgreSQL |
| Migrations | Alembic |
| Containerization | Docker |

---

# Project Structure

```text
backend/
├── app/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── scripts/
│   └── main.py
│
├── alembic/
├── scripts/
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

# Authentication Model

## VPN Applicants

Users authenticate using Active Directory credentials.

Example:

```text
student1@hightech.local
password
```

The backend performs an LDAPS bind against the domain controller.

Passwords are never stored.

---

## Console Users

Administrative users are stored locally in PostgreSQL.

Supported roles:

- ADMIN
- SECURITY_ANALYST
- AUDITOR

Authentication flow:

```text
Username + Password
        ↓
Password Verification (bcrypt)
        ↓
JWT Access Token
        ↓
Protected API Access
```

---

# RBAC Matrix

| Action | Admin | Analyst | Auditor |
|----------|---------|---------|---------|
| Approve Requests | ✅ | ❌ | ❌ |
| Reject Requests | ✅ | ❌ | ❌ |
| View Requests | ✅ | ✅ | ❌ |
| View VPN Users | ✅ | ✅ | ❌ |
| Revoke VPN Access | ✅ | ❌ | ❌ |
| View Alerts | ✅ | ✅ | ✅ |
| Resolve Alerts | ✅ | ✅ | ❌ |
| Block Devices | ✅ | ✅ | ❌ |
| View Audit Logs | ✅ | ✅ | ✅ |
| Manage Users | ✅ | ❌ | ❌ |

---

# Database Entities

## Core Tables

- application_users
- vpn_requests
- audit_logs

## Monitoring Tables

- vpn_sessions
- traffic_stats
- auth_events
- security_alerts
- blocked_devices
- script_state

---

# API Endpoints

## Authentication

| Method | Endpoint |
|----------|----------|
| POST | `/auth/login` |
| POST | `/auth/refresh` |

---

## VPN Requests

| Method | Endpoint |
|----------|----------|
| POST | `/vpn/request` |
| GET | `/requests` |
| GET | `/requests/{id}` |
| POST | `/requests/{id}/approve` |
| POST | `/requests/{id}/reject` |

---

## VPN Access Management

| Method | Endpoint |
|----------|----------|
| GET | `/vpn-users` |
| DELETE | `/vpn-users/{username}` |

---

## Monitoring

| Method | Endpoint |
|----------|----------|
| GET | `/monitoring/overview` |
| GET | `/alerts` |
| GET | `/logs` |

---

## Device Blocking

| Method | Endpoint |
|----------|----------|
| GET | `/blocked-devices` |
| POST | `/blocked-devices` |
| POST | `/blocked-devices/{id}/unblock` |

---

## User Management

| Method | Endpoint |
|----------|----------|
| POST | `/users` |
| GET | `/users` |
| PUT | `/users/{id}/role` |
| PATCH | `/users/{id}/activate` |
| PATCH | `/users/{id}/deactivate` |

---

# Environment Variables

Create a `.env` file:

```env
APP_ENV=development

DATABASE_URL=postgresql://postgres:password@localhost:5432/sentinel_vac

SECRET_KEY=CHANGE_ME
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

LDAP_SERVER=dc01.hightech.local
LDAP_PORT=636
LDAP_USE_SSL=true

LDAP_BIND_USER=vpnsvc@hightech.local
LDAP_BIND_PASSWORD=ChangeMe

LDAP_BASE_DN=DC=hightech,DC=local

VPN_GROUP=VPN_Users

OPENVPN_STATUS_FILE=/var/log/openvpn-status.log
AUTH_LOG_FILE=/var/log/auth.log
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-org/sentinel-vac-backend.git

cd sentinel-vac-backend
```

---

## Create Virtual Environment

```bash
python -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Database Migrations

```bash
alembic upgrade head
```

---

## Create Initial Admin

```bash
python scripts/seed_admin.py
```

---

## Start API

```bash
uvicorn app.main:app --reload
```

API:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

---

# Monitoring Scripts

These scripts run independently from FastAPI.

| Script | Purpose |
|----------|----------|
| collect_vpn_sessions.py | VPN session collection |
| collect_auth_events.py | Authentication monitoring |
| detect_alerts.py | Threat detection |
| enforce_ufw.py | Firewall enforcement |

Example:

```bash
python -m app.scripts.collect_vpn_sessions
```

---

# Security Notes

### Active Directory

- LDAPS only
- No password storage
- Least-privilege service account

### JWT

- Short-lived access tokens
- Refresh token rotation

### Password Storage

- bcrypt hashing
- No plaintext passwords

### Audit Logging

All security-sensitive actions are recorded.

---

# Future Enhancements

- MFA Integration
- Access Expiration Policies
- Email Notifications
- Wazuh Integration
- ELK Stack Integration
- Risk-Based Access Approval
- SIEM Connectivity

---

# License

Educational and research purposes only.

---

# Related Components

- Sentinel VAC Frontend (React)
- OpenVPN Server
- Active Directory Domain Services
- PostgreSQL Database
