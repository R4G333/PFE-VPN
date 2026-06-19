# Sentinel VAC Frontend

Frontend application for Sentinel VAC (VPN Access Control).

Built with React and TailwindCSS, the frontend provides a centralized interface for VPN access requests, administration, monitoring, and security operations.

---

## Overview

The frontend offers two main interfaces:

### VPN Request Portal

For Active Directory users requesting VPN access.

### Administration Console

For security teams managing:

- VPN requests
- Active Directory VPN users
- Security alerts
- Blocked devices
- Audit logs
- User management

---

## Features

### VPN Access Requests

- Submit VPN access requests
- Active Directory credential validation
- Request status tracking

### Dashboard

- System overview
- Active VPN users
- Security alerts
- Traffic statistics

### VPN User Management

- View VPN authorized users
- Revoke VPN access

### Security Monitoring

- VPN sessions
- Authentication events
- Brute-force alerts
- Password spraying alerts

### Device Blocking

- View blocked devices
- Block suspicious IPs
- Unblock devices

### Administration

- User management
- Role management
- Audit logs

---

## Technology Stack

| Component | Technology |
|------------|------------|
| Framework | React |
| Build Tool | Vite |
| Styling | TailwindCSS |
| Routing | React Router |
| HTTP Client | Axios |
| State Management | Context API |
| Authentication | JWT |

---

## Architecture

```text
React SPA
     │
     ▼
Axios API Client
     │
     ▼
FastAPI Backend
     │
     ▼
PostgreSQL
```

---

## Project Structure

```text
frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── contexts/
│   ├── hooks/
│   ├── layouts/
│   ├── pages/
│   ├── routes/
│   ├── services/
│   └── utils/
│
├── public/
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## User Roles

### Administrator

Access to:

- Request management
- User management
- Role management
- Monitoring
- Alerts
- Blocked devices
- Audit logs

### Security Analyst

Access to:

- Requests
- Monitoring
- Alerts
- Blocked devices

### Auditor

Read-only access to:

- Monitoring
- Audit logs
- Security alerts

---

## Main Pages

### Authentication

- Login
- Session management

### Dashboard

- Overview cards
- Active sessions
- Alert summaries

### VPN Requests

- Pending requests
- Approved requests
- Rejected requests

### VPN Users

- Authorized VPN users
- Revoke access

### Monitoring

- VPN sessions
- Traffic statistics
- Authentication activity

### Security Alerts

- Brute-force detection
- Password spraying detection
- Alert resolution

### Blocked Devices

- Blocked IPs
- Device management

### Audit Logs

- Administrative activity
- Security events

### User Management

- Create users
- Assign roles
- Activate/deactivate accounts

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-org/sentinel-vac-frontend.git

cd sentinel-vac-frontend
```

### Install Dependencies

```bash
npm install
```

### Configure Environment

Create:

```env
VITE_API_URL=http://localhost:8000/api
```

### Start Development Server

```bash
npm run dev
```

Application:

```text
http://localhost:5173
```

---

## Build

```bash
npm run build
```

Production files:

```text
dist/
```

---

## Backend Dependency

The frontend requires the Sentinel VAC Backend API.

Backend must be running before login and management features are available.

---

## Security Features

- JWT authentication
- Role-based navigation
- Protected routes
- Automatic token refresh
- Secure API communication

---

## Screenshots

```text
docs/screenshots/
├── login.png
├── dashboard.png
├── requests.png
├── monitoring.png
└── alerts.png
```

Add screenshots here after deployment.

---

## License

Educational and research purposes only.
