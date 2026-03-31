from pydantic import BaseModel


class UserSessionItem(BaseModel):
    id: str
    is_active: bool
    login_ip: str | None
    last_seen_ip: str | None
    user_agent: str | None
    created_at: str
    expires_at: str | None
    last_seen_at: str | None
    revoked_at: str | None


class UserSessionsResponse(BaseModel):
    items: list[UserSessionItem]
    total: int