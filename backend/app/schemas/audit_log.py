from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    actor: str
    action: str
    target: str
    detail: str | None
    ip_address: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogResponse]