from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from shared.solar_common import AuditLog


def record_audit(
    db: Session,
    *,
    actor: str,
    actor_role: str,
    service: str,
    action: str,
    resource: str,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
) -> AuditLog:
    item = AuditLog(
        actor=actor,
        actor_role=actor_role,
        service=service,
        action=action,
        resource=resource,
        outcome=outcome,
        details=details or {},
    )
    db.add(item)
    db.flush()
    return item

