from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.api.v1.endpoints.auth import get_current_user


def require_permission(permission_code: str) -> Callable:
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Super admin bypass
        if current_user.is_super_admin:
            return current_user

        # Load role with permissions
        role = (
            db.query(Role)
            .filter(Role.name == current_user.role)
            .first()
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role not found",
            )

        permission_codes = {perm.code for perm in role.permissions}

        if permission_code not in permission_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return checker