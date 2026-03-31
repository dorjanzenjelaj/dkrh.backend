from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User


def log_activity(
    db: Session,
    *,
    actor: User | None,
    action_type: str,
    entity_type: str,
    entity_id: str | None,
    entity_label: str | None = None,
    route: str | None = None,
    method: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    before_json: dict | None = None,
    after_json: dict | None = None,
    metadata_json: dict | None = None,
) -> None:
    db.add(
        ActivityLog(
            actor_user_id=actor.id if actor else None,
            actor_role_snapshot=actor.role.code if actor and actor.role else None,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_label=entity_label,
            route=route,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )
    )
    db.commit()