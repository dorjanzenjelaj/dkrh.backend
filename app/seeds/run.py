from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.seeds.permissions import PERMISSIONS
from app.seeds.role_permissions import ROLE_PERMISSION_MAP
from app.seeds.roles import ROLES


def seed_roles(db: Session) -> None:
    for role_data in ROLES:
        existing = db.execute(
            select(Role).where(Role.code == role_data["code"])
        ).scalar_one_or_none()

        if not existing:
            db.add(Role(**role_data))

    db.commit()


def seed_permissions(db: Session) -> None:
    for permission_data in PERMISSIONS:
        existing = db.execute(
            select(Permission).where(Permission.code == permission_data["code"])
        ).scalar_one_or_none()

        if not existing:
            db.add(Permission(**permission_data))

    db.commit()


def seed_role_permissions(db: Session) -> None:
    roles = {
        role.code: role
        for role in db.execute(select(Role)).scalars().all()
    }
    permissions = {
        permission.code: permission
        for permission in db.execute(select(Permission)).scalars().all()
    }

    for role_code, permission_codes in ROLE_PERMISSION_MAP.items():
        role = roles.get(role_code)
        if not role:
            continue

        for permission_code in permission_codes:
            permission = permissions.get(permission_code)
            if not permission:
                continue

            existing = db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            ).scalar_one_or_none()

            if not existing:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

    db.commit()


def seed_super_admin(
    db: Session,
    username: str,
    email: str,
    full_name: str,
    password: str,
) -> None:
    existing = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if existing:
        return

    admin_role = db.execute(
        select(Role).where(Role.code == "admin")
    ).scalar_one()

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        role_id=admin_role.id,
        is_super_admin=True,
        must_change_password=False,
        status="active",
    )
    db.add(user)
    db.commit()