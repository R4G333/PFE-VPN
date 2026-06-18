import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    alerts,
    audit_logs,
    auth,
    blocked_devices,
    monitoring,
    users,
    vpn_requests,
    vpn_users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Secure Remote Access Management Platform",
        description=(
            "Manages VPN access requests via Active Directory. "
            "Applicants authenticate with AD credentials; admins/analysts "
            "review and approve/reject requests."
        ),
        version="1.0.0",
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(vpn_requests.router)
    app.include_router(audit_logs.router)
    app.include_router(monitoring.router)
    app.include_router(vpn_users.router)
    app.include_router(blocked_devices.router)
    app.include_router(alerts.router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()