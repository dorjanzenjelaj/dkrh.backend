from pydantic import BaseModel, EmailStr


class UserListItem(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    status: str
    role: str
    is_super_admin: bool
    must_change_password: bool


class UserDetailResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    phone: str | None
    status: str
    role: str
    is_super_admin: bool
    must_change_password: bool
    created_at: str
    updated_at: str
    last_login_at: str | None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int