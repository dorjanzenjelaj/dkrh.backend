import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.dependencies.db import get_db
from app.dependencies.rbac import require_permission
from app.models.user import User
from app.schemas.user import UserDetailResponse, UserListItem, UserListResponse

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