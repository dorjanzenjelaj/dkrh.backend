from pydantic import BaseModel, EmailStr, Field


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

class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    role_code: str
    password: str = Field(min_length=8, max_length=128)
    is_super_admin: bool = False

class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    role_code: str | None = None
    status: str | None = None
    is_super_admin: bool | None = None

class UserActionResponse(BaseModel):
    id: str
    message: str

class UserResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
    must_change_password: bool = True