import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserStatus
from app.core.security import hash_password
from app.dependencies.db import get_db
from app.dependencies.rbac import require_permission
from app.models.role import Role
from app.models.user import User
from app.schemas.user import (
    UserActionResponse,
    UserCreateRequest,
    UserDetailResponse,
    UserListItem,
    UserListResponse,
    UserUpdateRequest,
)
from app.services.activity_log_service import log_activity

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    role: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    _: User = Depends(require_permission("users.view")),
    db: Session = Depends(get_db),
):
    filters = [User.deleted_at.is_(None)]

    if q:
        search = f"%{q.strip()}%"
        filters.append(
            or_(
                User.username.ilike(search),
                User.email.ilike(search),
                User.full_name.ilike(search),
            )
        )

    if status_filter:
        filters.append(User.status == status_filter)

    base_query = (
        select(User)
        .options(joinedload(User.role))
        .where(*filters)
        .order_by(User.created_at.desc())
    )

    if role:
        base_query = base_query.where(User.role.has(code=role))

    total = db.execute(
        select(func.count())
        .select_from(User)
        .where(*filters)
        .where(User.role.has(code=role) if role else True)
    ).scalar_one()

    users = db.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    items = [
        UserListItem(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            status=str(user.status),
            role=user.role.code,
            is_super_admin=user.is_super_admin,
            must_change_password=user.must_change_password,
        )
        for user in users
    ]

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: uuid.UUID,
    _: User = Depends(require_permission("users.view")),
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User)
        .options(joinedload(User.role))
        .where(User.id == user_id, User.deleted_at.is_(None))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserDetailResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=str(user.status),
        role=user.role.code,
        is_super_admin=user.is_super_admin,
        must_change_password=user.must_change_password,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )





@router.post("", response_model=UserActionResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_permission("users.create")),
    db: Session = Depends(get_db),
):
    existing_username = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")

    existing_email = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    role = db.execute(
        select(Role).where(Role.code == payload.role_code)
    ).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    new_user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        status=UserStatus.ACTIVE.value,
        role_id=role.id,
        created_by=current_user.id,
        updated_by=current_user.id,
        is_super_admin=payload.is_super_admin if current_user.is_super_admin else False,
        must_change_password=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_activity(
        db,
        actor=current_user,
        action_type="user_created",
        entity_type="user",
        entity_id=str(new_user.id),
        entity_label=new_user.username,
        route=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        after_json={
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "phone": new_user.phone,
            "status": new_user.status,
            "role": role.code,
            "is_super_admin": new_user.is_super_admin,
        },
    )

    return UserActionResponse(
        id=str(new_user.id),
        message="User created successfully",
    )


@router.put("/{user_id}", response_model=UserActionResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(require_permission("users.edit")),
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User).options(joinedload(User.role)).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before_json = {
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "status": user.status,
        "role": user.role.code if user.role else None,
        "is_super_admin": user.is_super_admin,
    }

    if payload.email is not None and payload.email != user.email:
        existing_email = db.execute(
            select(User).where(User.email == payload.email, User.id != user.id)
        ).scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = payload.email

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.phone is not None:
        user.phone = payload.phone

    if payload.status is not None:
        allowed_statuses = {item.value for item in UserStatus}
        if payload.status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        user.status = payload.status

    if payload.role_code is not None:
        role = db.execute(
            select(Role).where(Role.code == payload.role_code)
        ).scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role_id = role.id

    if payload.is_super_admin is not None:
        if not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="Only super admin can change super admin flag")
        user.is_super_admin = payload.is_super_admin

    user.updated_by = current_user.id
    db.commit()
    db.refresh(user)

    role_code = user.role.code if user.role else None

    log_activity(
        db,
        actor=current_user,
        action_type="user_updated",
        entity_type="user",
        entity_id=str(user.id),
        entity_label=user.username,
        route=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        before_json=before_json,
        after_json={
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "status": user.status,
            "role": role_code,
            "is_super_admin": user.is_super_admin,
        },
    )

    return UserActionResponse(
        id=str(user.id),
        message="User updated successfully",
    )


@router.post("/{user_id}/deactivate", response_model=UserActionResponse)
def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("users.deactivate")),
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User).options(joinedload(User.role)).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")

    before_json = {
        "status": user.status,
        "role": user.role.code if user.role else None,
    }

    user.status = UserStatus.INACTIVE.value
    user.updated_by = current_user.id
    db.commit()
    db.refresh(user)

    log_activity(
        db,
        actor=current_user,
        action_type="user_deactivated",
        entity_type="user",
        entity_id=str(user.id),
        entity_label=user.username,
        route=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        before_json=before_json,
        after_json={"status": user.status},
    )

    return UserActionResponse(
        id=str(user.id),
        message="User deactivated successfully",
    )