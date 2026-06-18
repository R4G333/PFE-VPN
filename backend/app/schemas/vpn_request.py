from datetime import datetime

from pydantic import BaseModel, Field

from app.models.vpn_request import RequestStatus


class VpnRequestCreate(BaseModel):
    """
    Submitted by an AD user — password is used only for LDAP bind
    and is NEVER persisted anywhere.
    """
    ad_username: str = Field(..., min_length=1, max_length=255)
    ad_password: str = Field(..., min_length=1)


class VpnRequestReject(BaseModel):
    rejection_reason: str = Field(..., min_length=1, max_length=1000)


class VpnRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    ad_username: str
    display_name: str
    status: RequestStatus
    reviewed_by: str | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime


class VpnRequestListResponse(BaseModel):
    total: int
    items: list[VpnRequestResponse]