from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.auth_service import (
    authenticate_user,
    create_user_session,
    log_security_event,
    refresh_user_session
)

from datetime import datetime, timezone


from app.models.session import Session as UserSession
from app.schemas.auth import RefreshTokenRequest, TokenPairResponse


from app.schemas.session import UserSessionItem, UserSessionsResponse
from sqlalchemy import select
from app.dependencies.auth import get_current_user, get_current_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not user:
        log_security_event(
            db,
            user_id=None,
            session_id=None,
            event_type="login_failed",
            result="failure",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={"username": payload.username},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token, refresh_token = create_user_session(
        db=db,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    log_security_event(
        db,
        user_id=user.id,
        session_id=None,
        event_type="login_success",
        result="success",
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json={"username": user.username},
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.code,
        is_super_admin=current_user.is_super_admin,
    )




@router.post("/refresh", response_model=TokenPairResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        access_token, refresh_token, user = refresh_user_session(
            db=db,
            refresh_token=payload.refresh_token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    current_session.is_active = False
    current_session.revoked_at = datetime.now(timezone.utc)
    current_session.revoked_by = current_user.id

    log_security_event(
        db,
        user_id=current_user.id,
        session_id=current_session.id,
        event_type="logout",
        result="success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return {"message": "Logged out successfully"}


@router.get("/sessions", response_model=UserSessionsResponse)
def my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.execute(
        select(UserSession)
        .where(UserSession.user_id == current_user.id)
        .order_by(UserSession.created_at.desc())
    ).scalars().all()

    items = [
        UserSessionItem(
            id=str(s.id),
            is_active=s.is_active,
            login_ip=s.login_ip,
            last_seen_ip=s.last_seen_ip,
            user_agent=s.user_agent,
            created_at=s.created_at.isoformat(),
            expires_at=s.expires_at.isoformat() if s.expires_at else None,
            last_seen_at=s.last_seen_at.isoformat() if s.last_seen_at else None,
            revoked_at=s.revoked_at.isoformat() if s.revoked_at else None,
        )
        for s in sessions
    ]

    return UserSessionsResponse(
        items=items,
        total=len(items),
    )