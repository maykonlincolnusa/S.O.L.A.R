from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

from shared.audit import record_audit
from shared.solar_common import AuditLog, SessionLocal, audit_to_dict
from services.gateway.app.agent import answer_question
from services.gateway.app.security import Principal, get_principal, require_permission

router = APIRouter(tags=["gateway"])

INGESTION_URL = os.getenv("INGESTION_URL", "http://ingestion:8001")
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://analytics:8002")
SEMANTIC_URL = os.getenv("SEMANTIC_URL", "http://semantic:8003")
ALERTING_URL = os.getenv("ALERTING_URL", "http://alerting:8004")
INGESTION_SOURCE_MAP = {
    "camera": "camera",
    "public-data": "public_data",
    "public_data": "public_data",
    "police-records": "police_records",
    "police_records": "police_records",
    "gps": "gps_tracking",
    "gps_tracking": "gps_tracking",
    "ocr-plate": "plate_ocr",
    "plate_ocr": "plate_ocr",
}


class ChatPayload(BaseModel):
    question: str = Field(min_length=2, max_length=2000)


class RetentionPayload(BaseModel):
    days: int = Field(default=180, ge=1, le=3650)


class ApproveAlertPayload(BaseModel):
    approved_by: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=500)


async def _request(
    method: str,
    url: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.request(method, url, json=json, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text or str(exc)
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        return response.json()


def _record_gateway_audit(
    principal: Principal,
    *,
    action: str,
    resource: str,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    db = SessionLocal()
    try:
        record_audit(
            db,
            actor=principal.actor,
            actor_role=principal.role,
            service="gateway",
            action=action,
            resource=resource,
            outcome=outcome,
            details=details,
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


async def _proxy_with_audit(
    principal: Principal,
    *,
    method: str,
    url: str,
    action: str,
    resource: str,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        body = await _request(method, url, json=json, params=params)
        _record_gateway_audit(
            principal,
            action=action,
            resource=resource,
            details={"target": url, "method": method},
        )
        return body
    except HTTPException as exc:
        _record_gateway_audit(
            principal,
            action=action,
            resource=resource,
            outcome="error",
            details={"target": url, "method": method, "status_code": exc.status_code},
        )
        raise


@router.get("/api/security/whoami")
async def whoami(principal: Principal = Depends(get_principal)) -> dict[str, Any]:
    _record_gateway_audit(principal, action="security.whoami", resource="/api/security/whoami")
    return {
        "actor": principal.actor,
        "role": principal.role,
        "permissions": sorted(list(principal.permissions)),
        "token_hint": principal.token_hint,
    }


@router.get("/api/audit/logs")
async def audit_logs(
    actor: str | None = None,
    outcome: str | None = Query(default=None, pattern="^(success|error)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    principal: Principal = Depends(require_permission("audit.read")),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
        if actor:
            stmt = select(AuditLog).where(AuditLog.actor == actor).order_by(desc(AuditLog.created_at)).limit(limit)
        if outcome:
            stmt = (
                select(AuditLog)
                .where(AuditLog.outcome == outcome)
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            )
            if actor:
                stmt = (
                    select(AuditLog)
                    .where(AuditLog.actor == actor, AuditLog.outcome == outcome)
                    .order_by(desc(AuditLog.created_at))
                    .limit(limit)
                )
        rows = list(db.execute(stmt).scalars().all())
    finally:
        db.close()

    _record_gateway_audit(principal, action="audit.read", resource="/api/audit/logs")
    return {"count": len(rows), "items": [audit_to_dict(row) for row in rows]}


@router.post("/api/ingest/{source_type}")
async def ingest(
    source_type: str,
    payload: dict[str, Any],
    principal: Principal = Depends(require_permission("ingest.write")),
) -> dict[str, Any]:
    normalized_source = INGESTION_SOURCE_MAP.get(source_type, source_type)
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{INGESTION_URL}/ingest/{normalized_source}",
        action="ingest.write",
        resource=f"/api/ingest/{normalized_source}",
        json=payload,
    )


@router.get("/api/events")
async def events(
    limit: int = Query(default=100, ge=1, le=1000),
    principal: Principal = Depends(require_permission("events.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{INGESTION_URL}/ingest/events",
        action="events.read",
        resource="/api/events",
        params={"limit": limit},
    )


@router.get("/api/timeline")
async def timeline(
    limit: int = Query(default=200, ge=1, le=1000),
    principal: Principal = Depends(require_permission("events.read")),
) -> dict[str, Any]:
    return await events(limit=limit, principal=principal)


@router.get("/api/analytics/patterns")
async def patterns(
    hours: int = Query(default=24, ge=1, le=720),
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/patterns",
        action="analytics.patterns",
        resource="/api/analytics/patterns",
        params={"hours": hours},
    )


@router.get("/api/analytics/risk")
async def risk(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    params = {"hours": hours}
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/risk",
        action="analytics.risk",
        resource="/api/analytics/risk",
        params=params,
    )


@router.get("/api/analytics/ml/risk")
async def ml_risk(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    params = {"hours": hours}
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/ml/risk",
        action="analytics.ml_risk",
        resource="/api/analytics/ml/risk",
        params=params,
    )


@router.get("/api/analytics/deep/risk")
async def deep_risk(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    params = {"hours": hours}
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/deep/risk",
        action="analytics.deep_risk",
        resource="/api/analytics/deep/risk",
        params=params,
    )


@router.get("/api/analytics/models/compare")
async def compare_models(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    params = {"hours": hours}
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/models/compare",
        action="analytics.models_compare",
        resource="/api/analytics/models/compare",
        params=params,
    )


@router.post("/api/analytics/models/train")
async def train_models(
    payload: dict[str, Any],
    principal: Principal = Depends(require_permission("analytics.write")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{ANALYTICS_URL}/analytics/models/train",
        action="analytics.models_train",
        resource="/api/analytics/models/train",
        json=payload,
    )


@router.get("/api/analytics/models/registry")
async def model_registry(
    model_name: str | None = None,
    status: str | None = Query(default=None, pattern="^(trained|deployed|archived)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    include_artifacts: bool = False,
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit, "include_artifacts": include_artifacts}
    if model_name:
        params["model_name"] = model_name
    if status:
        params["status"] = status
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/models/registry",
        action="analytics.models_registry",
        resource="/api/analytics/models/registry",
        params=params,
    )


@router.patch("/api/analytics/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    principal: Principal = Depends(require_permission("analytics.write")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="PATCH",
        url=f"{ANALYTICS_URL}/analytics/models/{model_id}/deploy",
        action="analytics.model_deploy",
        resource=f"/api/analytics/models/{model_id}/deploy",
    )


@router.get("/api/analytics/models/deployed")
async def deployed_models(
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/models/deployed",
        action="analytics.models_deployed",
        resource="/api/analytics/models/deployed",
    )


@router.get("/api/analytics/clusters")
async def clusters(
    hours: int = Query(default=24, ge=1, le=720),
    precision: int = Query(default=2, ge=1, le=4),
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/clusters",
        action="analytics.clusters",
        resource="/api/analytics/clusters",
        params={"hours": hours, "precision": precision},
    )


@router.get("/api/analytics/anomalies")
async def anomalies(
    hours: int = Query(default=24, ge=1, le=720),
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/anomalies",
        action="analytics.anomalies",
        resource="/api/analytics/anomalies",
        params={"hours": hours},
    )


@router.get("/api/stream/signals")
async def stream_signals(
    limit: int = Query(default=100, ge=1, le=1000),
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ANALYTICS_URL}/analytics/realtime/signals",
        action="analytics.realtime_signals",
        resource="/api/stream/signals",
        params={"limit": limit},
    )


@router.get("/api/stream/health")
async def stream_health(
    principal: Principal = Depends(require_permission("analytics.read")),
) -> dict[str, Any]:
    ingestion = await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{INGESTION_URL}/ingest/stream/health",
        action="stream.health.read",
        resource="/api/stream/health",
    )
    processor: dict[str, Any] = {"status": "disabled"}
    try:
        processor = await _request("GET", "http://stream-processor:8005/health")
    except Exception:
        processor = {"status": "unavailable"}
    return {"ingestion_stream": ingestion, "stream_processor": processor}


@router.post("/api/semantic/entities")
async def semantic_entities(
    payload: dict[str, Any],
    principal: Principal = Depends(require_permission("semantic.read")),
) -> dict[str, Any]:
    if not principal.can("semantic.write"):
        raise HTTPException(status_code=403, detail="Permission denied: semantic.write required")
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{SEMANTIC_URL}/semantic/entities",
        action="semantic.entities.upsert",
        resource="/api/semantic/entities",
        json=payload,
    )


@router.post("/api/semantic/relations")
async def semantic_relations(
    payload: dict[str, Any],
    principal: Principal = Depends(require_permission("semantic.read")),
) -> dict[str, Any]:
    if not principal.can("semantic.write"):
        raise HTTPException(status_code=403, detail="Permission denied: semantic.write required")
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{SEMANTIC_URL}/semantic/relations",
        action="semantic.relations.create",
        resource="/api/semantic/relations",
        json=payload,
    )


@router.get("/api/semantic/context/{entity_id}")
async def semantic_context(
    entity_id: str,
    event_limit: int = Query(default=50, ge=1, le=500),
    principal: Principal = Depends(require_permission("semantic.read")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{SEMANTIC_URL}/semantic/context/{entity_id}",
        action="semantic.context.read",
        resource=f"/api/semantic/context/{entity_id}",
        params={"event_limit": event_limit},
    )


@router.post("/api/alerts/evaluate")
async def evaluate_alerts(
    payload: dict[str, Any],
    principal: Principal = Depends(require_permission("alerts.write")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{ALERTING_URL}/alerts/evaluate",
        action="alerts.evaluate",
        resource="/api/alerts/evaluate",
        json=payload,
    )


@router.get("/api/alerts")
async def list_alerts(
    status: str | None = Query(default=None, pattern="^(open|closed|pending_approval)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    principal: Principal = Depends(require_permission("alerts.read")),
) -> dict[str, Any]:
    params = {"limit": limit}
    if status:
        params["status"] = status
    return await _proxy_with_audit(
        principal,
        method="GET",
        url=f"{ALERTING_URL}/alerts",
        action="alerts.read",
        resource="/api/alerts",
        params=params,
    )


@router.patch("/api/alerts/{alert_id}/approve")
async def approve_alert(
    alert_id: str,
    payload: ApproveAlertPayload,
    principal: Principal = Depends(require_permission("alerts.approve")),
) -> dict[str, Any]:
    body = {
        "approved_by": payload.approved_by or principal.actor,
        "note": payload.note,
    }
    return await _proxy_with_audit(
        principal,
        method="PATCH",
        url=f"{ALERTING_URL}/alerts/{alert_id}/approve",
        action="alerts.approve",
        resource=f"/api/alerts/{alert_id}/approve",
        json=body,
    )


@router.patch("/api/alerts/{alert_id}/close")
async def close_alert(
    alert_id: str,
    principal: Principal = Depends(require_permission("alerts.write")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="PATCH",
        url=f"{ALERTING_URL}/alerts/{alert_id}/close",
        action="alerts.close",
        resource=f"/api/alerts/{alert_id}/close",
    )


@router.post("/api/compliance/erase-vehicle/{plate_text}")
async def erase_vehicle_plate(
    plate_text: str,
    principal: Principal = Depends(require_permission("compliance.write")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{INGESTION_URL}/ingest/compliance/erase-vehicle/{plate_text}",
        action="compliance.erase_vehicle",
        resource=f"/api/compliance/erase-vehicle/{plate_text}",
    )


@router.post("/api/compliance/retention")
async def run_retention(
    payload: RetentionPayload,
    principal: Principal = Depends(require_permission("compliance.write")),
) -> dict[str, Any]:
    return await _proxy_with_audit(
        principal,
        method="POST",
        url=f"{INGESTION_URL}/ingest/compliance/retention",
        action="compliance.retention",
        resource="/api/compliance/retention",
        json={"days": payload.days},
    )


@router.get("/api/map/tactical")
async def tactical_map(
    hours: int = Query(default=24, ge=1, le=720),
    principal: Principal = Depends(require_permission("map.read")),
) -> dict[str, Any]:
    try:
        events_task = _request("GET", f"{INGESTION_URL}/ingest/events", params={"limit": 300})
        clusters_task = _request(
            "GET",
            f"{ANALYTICS_URL}/analytics/clusters",
            params={"hours": hours, "precision": 2},
        )
        alerts_task = _request("GET", f"{ALERTING_URL}/alerts", params={"limit": 200})
        events_data, clusters_data, alerts_data = await asyncio.gather(events_task, clusters_task, alerts_task)
    except HTTPException as exc:
        _record_gateway_audit(
            principal,
            action="map.tactical.read",
            resource="/api/map/tactical",
            outcome="error",
            details={"status_code": exc.status_code},
        )
        raise

    events = events_data.get("events", [])
    clusters = clusters_data.get("clusters", [])
    alerts = [item for item in alerts_data.get("alerts", []) if item.get("status") != "closed"]

    features = []
    for event in events:
        lat = event.get("latitude")
        lon = event.get("longitude")
        if lat is None or lon is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "event_id": event.get("id"),
                    "source_type": event.get("source_type"),
                    "severity": event.get("severity"),
                    "occurred_at": event.get("occurred_at"),
                    "plate_text": event.get("plate_text"),
                },
            }
        )

    _record_gateway_audit(principal, action="map.tactical.read", resource="/api/map/tactical")
    return {
        "geojson": {"type": "FeatureCollection", "features": features},
        "clusters": clusters,
        "open_alerts": alerts,
        "summary": {
            "event_points": len(features),
            "cluster_count": len(clusters),
            "open_alert_count": len(alerts),
        },
    }


@router.post("/api/chat")
async def chat(
    payload: ChatPayload,
    principal: Principal = Depends(require_permission("chat.query")),
) -> dict[str, Any]:
    try:
        events_data, alerts_data = await asyncio.gather(
            _request("GET", f"{INGESTION_URL}/ingest/events", params={"limit": 200}),
            _request("GET", f"{ALERTING_URL}/alerts", params={"limit": 100}),
        )
        timeline = events_data.get("events", [])
        alerts = alerts_data.get("alerts", [])
        answer = await answer_question(payload.question, timeline=timeline, alerts=alerts)
    except HTTPException as exc:
        _record_gateway_audit(
            principal,
            action="chat.query",
            resource="/api/chat",
            outcome="error",
            details={"status_code": exc.status_code},
        )
        raise

    _record_gateway_audit(principal, action="chat.query", resource="/api/chat")
    return {"question": payload.question, **answer}
