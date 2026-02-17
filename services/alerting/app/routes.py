from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from shared.audit import record_audit
from shared.solar_common import Alert, get_db

router = APIRouter(prefix="/alerts", tags=["alerting"])

ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://analytics:8002")


class EvaluatePayload(BaseModel):
    lookback_hours: int = Field(default=24, ge=1, le=720)
    risk_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    anomaly_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    pattern_threshold: float = Field(default=0.75, ge=0.0, le=1.0)


class ApprovePayload(BaseModel):
    approved_by: str = Field(default="operator", min_length=2, max_length=128)
    note: str | None = Field(default=None, max_length=500)


def create_alert(
    db: Session,
    *,
    alert_type: str,
    priority: str,
    message: str,
    details: dict[str, Any],
) -> Alert:
    status = "pending_approval" if priority == "high" else "open"
    alert = Alert(
        alert_type=alert_type,
        priority=priority,
        status=status,
        message=message,
        details=details,
    )
    db.add(alert)
    db.flush()
    return alert


@router.post("/evaluate")
async def evaluate(payload: EvaluatePayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        risk_resp = await client.get(
            f"{ANALYTICS_URL}/analytics/risk",
            params={"hours": payload.lookback_hours},
        )
        risk_resp.raise_for_status()
        risk = risk_resp.json()

        anomalies_resp = await client.get(
            f"{ANALYTICS_URL}/analytics/anomalies",
            params={"hours": payload.lookback_hours},
        )
        anomalies_resp.raise_for_status()
        anomalies = anomalies_resp.json().get("anomalies", [])

        patterns_resp = await client.get(
            f"{ANALYTICS_URL}/analytics/patterns",
            params={"hours": payload.lookback_hours},
        )
        patterns_resp.raise_for_status()
        patterns = patterns_resp.json().get("patterns", [])

    created: list[dict[str, Any]] = []
    if risk.get("score", 0) >= payload.risk_threshold:
        level = "high" if risk["score"] >= 0.8 else "medium"
        alert = create_alert(
            db,
            alert_type="predictive_risk",
            priority=level,
            message=f"Risk score above threshold: {risk['score']}",
            details={"risk": risk, "evaluated_at": datetime.now(timezone.utc).isoformat()},
        )
        created.append(alert_to_dict(alert))

    for anomaly in anomalies:
        if anomaly.get("score", 0) < payload.anomaly_threshold:
            continue
        level = "high" if anomaly["score"] >= 0.9 else "medium"
        alert = create_alert(
            db,
            alert_type="anomaly",
            priority=level,
            message=f"Anomaly detected on event {anomaly.get('event_id')}",
            details={"anomaly": anomaly, "evaluated_at": datetime.now(timezone.utc).isoformat()},
        )
        created.append(alert_to_dict(alert))

    for pattern in patterns:
        if pattern.get("score", 0) < payload.pattern_threshold:
            continue
        level = "high" if pattern["score"] >= 0.9 else "medium"
        alert = create_alert(
            db,
            alert_type="pattern",
            priority=level,
            message=f"Pattern for plate {pattern.get('plate_text')} exceeded threshold",
            details={"pattern": pattern, "evaluated_at": datetime.now(timezone.utc).isoformat()},
        )
        created.append(alert_to_dict(alert))

    record_audit(
        db,
        actor="alerting-engine",
        actor_role="system",
        service="alerting",
        action="alerts.evaluate",
        resource="alerts:evaluation",
        details={
            "created_count": len(created),
            "lookback_hours": payload.lookback_hours,
            "anomaly_count": len(anomalies),
            "pattern_count": len(patterns),
            "risk_score": risk.get("score"),
        },
    )

    db.commit()

    return {
        "created_count": len(created),
        "alerts": created,
        "risk": risk,
        "anomaly_count": len(anomalies),
        "pattern_count": len(patterns),
    }


@router.get("")
def list_alerts(
    status: str | None = Query(default=None, pattern="^(open|closed|pending_approval)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    if status:
        stmt = select(Alert).where(Alert.status == status).order_by(desc(Alert.created_at)).limit(limit)
    alerts = db.execute(stmt).scalars().all()
    return {"count": len(alerts), "alerts": [alert_to_dict(alert) for alert in alerts]}


@router.patch("/{alert_id}/close")
def close_alert(alert_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status == "pending_approval":
        raise HTTPException(status_code=409, detail="High-priority alert requires approval before close")
    alert.status = "closed"
    details = dict(alert.details or {})
    details["closed_at"] = datetime.now(timezone.utc).isoformat()
    alert.details = details
    record_audit(
        db,
        actor="alert-operator",
        actor_role="operator",
        service="alerting",
        action="alerts.close",
        resource=f"alert:{alert.id}",
    )
    db.commit()
    db.refresh(alert)
    return {"status": "closed", "alert": alert_to_dict(alert)}


@router.patch("/{alert_id}/approve")
def approve_alert(alert_id: str, payload: ApprovePayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    details = dict(alert.details or {})
    details["approved_by"] = payload.approved_by
    details["approved_at"] = datetime.now(timezone.utc).isoformat()
    if payload.note:
        details["approval_note"] = payload.note
    alert.details = details
    alert.status = "open"

    record_audit(
        db,
        actor=payload.approved_by,
        actor_role="compliance",
        service="alerting",
        action="alerts.approve",
        resource=f"alert:{alert.id}",
        details={"note": payload.note} if payload.note else {},
    )
    db.commit()
    db.refresh(alert)
    return {"status": "approved", "alert": alert_to_dict(alert)}


def alert_to_dict(alert: Alert) -> dict[str, Any]:
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "priority": alert.priority,
        "status": alert.status,
        "message": alert.message,
        "details": alert.details or {},
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }
