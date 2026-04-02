import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_token, verify_password
from app.models.security_audit_log import SecurityAuditLog
from app.models.session import Session as UserSession
from app.models.user import User

from jose import JWTError, jwt


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.execute(
        select(User).where(User.username == username, User.deleted_at.is_(None))
    ).scalar_one_or_none()

    if not user:
        return None

    if user.status != "active":
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_user_session(
    db: Session,
    user: User,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str]:
    access_token = create_token(
        subject=str(user.id),
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        extra_claims={"type": "access", "username": user.username},
    )
    refresh_token = create_token(
        subject=str(user.id),
        expires_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        extra_claims={"type": "refresh", "username": user.username},
    )

    now = datetime.now(timezone.utc)

    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(access_token),
        refresh_token_hash=hash_token(refresh_token),
        login_ip=ip_address,
        last_seen_ip=ip_address,
        user_agent=user_agent,
        expires_at=now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    db.add(session)

    user.last_login_at = now
    user.last_login_ip = ip_address
    user.last_login_user_agent = user_agent
    user.failed_login_count = 0

    db.commit()

    return access_token, refresh_token


def log_security_event(
    db: Session,
    *,
    user_id,
    session_id,
    event_type: str,
    result: str,
    ip_address: str | None,
    user_agent: str | None,
    metadata_json: dict | None = None,
) -> None:
    db.add(
        SecurityAuditLog(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata_json,
        )
    )
    db.commit()


def refresh_user_session(
    db: Session,
    refresh_token: str,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str, User]:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")
    except JWTError:
        raise ValueError("Invalid refresh token")

    if not user_id or token_type != "refresh":
        raise ValueError("Invalid refresh token")

    session = db.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == hash_token(refresh_token),
            UserSession.user_id == user_id,
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if (
        not session
        or not session.is_active
        or session.revoked_at is not None
        or session.expires_at is None
        or session.expires_at < now
    ):
        raise ValueError("Refresh session expired or revoked")

    user = db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    ).scalar_one_or_none()

    if not user or user.status != "active":
        raise ValueError("Inactive or missing user")

    new_access_token = create_token(
        subject=str(user.id),
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        extra_claims={"type": "access", "username": user.username},
    )
    new_refresh_token = create_token(
        subject=str(user.id),
        expires_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        extra_claims={"type": "refresh", "username": user.username},
    )

    session.token_hash = hash_token(new_access_token)
    session.refresh_token_hash = hash_token(new_refresh_token)
    session.last_seen_ip = ip_address
    session.user_agent = user_agent
    session.expires_at = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    db.commit()

    return new_access_token, new_refresh_token, user