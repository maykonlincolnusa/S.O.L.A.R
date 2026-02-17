from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, desc, func, or_, select
from sqlalchemy.orm import Session

from shared.audit import record_audit
from shared.solar_common import (
    AnalyticsResult,
    AuditLog,
    Entity,
    EntityRelation,
    Event,
    event_to_dict,
    get_db,
    get_entity_by_type_and_label,
)
from shared.streaming import publish_event, stream_health

router = APIRouter(prefix="/ingest", tags=["ingestion"])

ALLOWED_SOURCES = {"camera", "public_data", "police_records", "gps_tracking", "plate_ocr"}
SOURCE_ALIASES = {
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

LGPD_STRICT_MODE = os.getenv("LGPD_STRICT_MODE", "true").lower() in {"1", "true", "yes"}
HASH_PLATE_TEXT = os.getenv("HASH_PLATE_TEXT", "true").lower() in {"1", "true", "yes"}
PII_HASH_SALT = os.getenv("PII_HASH_SALT", "solar-dev-salt")
PII_KEYS = {"cpf", "rg", "ssn", "full_name", "nome_completo", "phone", "email", "address"}


def _hash_value(value: str) -> str:
    digest = hashlib.sha256(f"{PII_HASH_SALT}:{value}".encode("utf-8")).hexdigest()
    return f"h_{digest[:16]}"


def _sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        lowered = key.lower()
        if lowered in PII_KEYS:
            sanitized[key] = "[redacted]"
            continue
        if isinstance(value, dict):
            sanitized[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, dict):
                    items.append(_sanitize_dict(item))
                else:
                    items.append(item)
            sanitized[key] = items
        else:
            sanitized[key] = value
    return sanitized


def _mask_plate_if_needed(plate_text: str | None) -> str | None:
    if not plate_text:
        return plate_text
    if LGPD_STRICT_MODE and HASH_PLATE_TEXT:
        return _hash_value(plate_text.upper().strip())
    return plate_text.upper().strip()


class IngestPayload(BaseModel):
    occurred_at: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    plate_text: str | None = Field(default=None, max_length=32)
    device_id: str | None = Field(default=None, max_length=64)
    severity: int = Field(default=1, ge=1, le=5)
    metadata: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class RetentionPayload(BaseModel):
    days: int = Field(default=180, ge=1, le=3650)


def upsert_entity(db: Session, entity_type: str, label: str, attributes: dict[str, Any]) -> Entity:
    existing = get_entity_by_type_and_label(db, entity_type, label)
    if existing:
        merged = dict(existing.attributes or {})
        merged.update(attributes)
        existing.attributes = merged
        db.flush()
        return existing

    entity = Entity(entity_type=entity_type, label=label, attributes=attributes)
    db.add(entity)
    db.flush()
    return entity


def ensure_vehicle_device_relation(db: Session, vehicle: Entity, device: Entity) -> None:
    stmt = select(EntityRelation).where(
        EntityRelation.source_entity_id == vehicle.id,
        EntityRelation.target_entity_id == device.id,
        EntityRelation.relation_type == "detected_by",
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        return
    db.add(
        EntityRelation(
            source_entity_id=vehicle.id,
            target_entity_id=device.id,
            relation_type="detected_by",
            confidence=0.7,
        )
    )


def ingest_event_internal(source_type: str, payload: IngestPayload, db: Session) -> dict[str, Any]:
    source_type = SOURCE_ALIASES.get(source_type, source_type)
    if source_type not in ALLOWED_SOURCES:
        raise HTTPException(status_code=400, detail=f"Unsupported source_type: {source_type}")

    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    normalized_plate = _mask_plate_if_needed(payload.plate_text)
    metadata = _sanitize_dict(payload.metadata) if LGPD_STRICT_MODE else payload.metadata
    raw_payload = _sanitize_dict(payload.payload) if LGPD_STRICT_MODE else payload.payload

    event = Event(
        source_type=source_type,
        occurred_at=occurred_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        plate_text=normalized_plate,
        device_id=payload.device_id,
        severity=payload.severity,
        meta=metadata,
        raw_payload=raw_payload,
    )
    db.add(event)
    db.flush()

    vehicle_entity = None
    device_entity = None
    if normalized_plate:
        vehicle_entity = upsert_entity(
            db,
            entity_type="vehicle",
            label=normalized_plate,
            attributes={"plate_text": normalized_plate},
        )
    if payload.device_id:
        device_entity = upsert_entity(
            db,
            entity_type="sensor_device",
            label=payload.device_id,
            attributes={"device_id": payload.device_id},
        )
    if vehicle_entity and device_entity:
        ensure_vehicle_device_relation(db, vehicle_entity, device_entity)

    record_audit(
        db,
        actor=str(metadata.get("operator", "ingestion-api")),
        actor_role="system",
        service="ingestion",
        action="event.ingested",
        resource=f"event:{event.id}",
        details={"source_type": source_type, "severity": payload.severity},
    )

    db.commit()
    db.refresh(event)
    stream_ok = publish_event(event_to_dict(event))

    return {"status": "ingested", "event": event_to_dict(event), "stream_published": stream_ok}


@router.post("/{source_type}")
def ingest_event(source_type: str, payload: IngestPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ingest_event_internal(source_type, payload, db)


@router.post("/camera")
def ingest_camera(payload: IngestPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ingest_event_internal("camera", payload, db)


@router.post("/public-data")
def ingest_public_data(payload: IngestPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ingest_event_internal("public_data", payload, db)


@router.post("/police-records")
def ingest_police_records(payload: IngestPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ingest_event_internal("police_records", payload, db)


@router.post("/gps")
def ingest_gps(payload: IngestPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ingest_event_internal("gps_tracking", payload, db)


@router.post("/ocr-plate")
def ingest_ocr_plate(payload: IngestPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ingest_event_internal("plate_ocr", payload, db)


@router.get("/events")
def list_events(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)) -> dict[str, Any]:
    stmt = select(Event).order_by(desc(Event.occurred_at)).limit(limit)
    events = db.execute(stmt).scalars().all()
    return {"count": len(events), "events": [event_to_dict(event) for event in events]}


@router.get("/stream/health")
def ingest_stream_health() -> dict[str, Any]:
    return stream_health()


@router.post("/compliance/erase-vehicle/{plate_text}")
def compliance_erase_vehicle(plate_text: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    normalized = plate_text.upper().strip()
    candidates = {normalized, _hash_value(normalized), _mask_plate_if_needed(normalized)}
    candidates = {value for value in candidates if value}

    events_stmt = select(Event).where(Event.plate_text.in_(list(candidates)))
    entity_stmt = select(Entity).where(
        Entity.entity_type == "vehicle",
        Entity.label.in_(list(candidates)),
    )
    events = list(db.execute(events_stmt).scalars().all())
    entities = list(db.execute(entity_stmt).scalars().all())

    for event in events:
        event.plate_text = None
        meta = dict(event.meta or {})
        meta["plate_erased"] = True
        event.meta = meta

    for entity in entities:
        attrs = dict(entity.attributes or {})
        attrs["plate_text"] = None
        attrs["erased"] = True
        entity.attributes = attrs
        entity.label = f"erased:{entity.id[:8]}"

    record_audit(
        db,
        actor="compliance-system",
        actor_role="compliance",
        service="ingestion",
        action="compliance.erase_vehicle",
        resource=f"plate:{normalized}",
        details={"event_count": len(events), "entity_count": len(entities)},
    )
    db.commit()

    return {
        "status": "ok",
        "erased_events": len(events),
        "erased_entities": len(entities),
    }


@router.post("/compliance/retention")
def compliance_retention(payload: RetentionPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=payload.days)

    event_count = db.execute(select(func.count(Event.id)).where(Event.occurred_at < cutoff)).scalar() or 0
    old_event_ids = select(Event.id).where(Event.occurred_at < cutoff)
    analytics_count = (
        db.execute(
            select(func.count(AnalyticsResult.id)).where(
                or_(AnalyticsResult.created_at < cutoff, AnalyticsResult.event_id.in_(old_event_ids))
            )
        ).scalar()
        or 0
    )
    audit_count = db.execute(select(func.count(AuditLog.id)).where(AuditLog.created_at < cutoff)).scalar() or 0

    db.execute(
        delete(AnalyticsResult).where(
            or_(AnalyticsResult.created_at < cutoff, AnalyticsResult.event_id.in_(old_event_ids))
        )
    )
    db.execute(delete(Event).where(Event.occurred_at < cutoff))
    db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))

    record_audit(
        db,
        actor="compliance-system",
        actor_role="compliance",
        service="ingestion",
        action="compliance.retention",
        resource=f"older_than:{payload.days}d",
        details={
            "deleted_events": int(event_count),
            "deleted_analytics_results": int(analytics_count),
            "deleted_audit_logs": int(audit_count),
        },
    )
    db.commit()

    return {
        "status": "ok",
        "retention_days": payload.days,
        "deleted_events": int(event_count),
        "deleted_analytics_results": int(analytics_count),
        "deleted_audit_logs": int(audit_count),
    }
