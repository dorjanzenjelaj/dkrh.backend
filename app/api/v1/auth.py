from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.auth_service import (
    authenticate_user,
    create_user_session,
    log_security_event,
)

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