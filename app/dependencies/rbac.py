from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User


def require_permission(permission_code: str) -> Callable:
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Admin bypass
        if current_user.is_super_admin:
            return current_user

        # System admin role bypass
        if current_user.role and current_user.role.code == "admin":
            return current_user

        has_permission = db.execute(
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == current_user.role_id,
                Permission.code == permission_code,
            )
        ).first()

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission_code}",
            )

        return current_user

    return dependency