import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SecurityEventResult
from app.models.base import Base


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    result: Mapped[SecurityEventResult] = mapped_column(
        String(20),
        nullable=False,
        default=SecurityEventResult.SUCCESS.value,
        server_default=SecurityEventResult.SUCCESS.value,
    )

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="security_audit_logs")
    session = relationship("Session", back_populates="security_audit_logs")