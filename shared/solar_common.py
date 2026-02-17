from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://solar:solar123@localhost:5432/solar",
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    plate_text: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=1)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(128), index=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class EntityRelation(Base):
    __tablename__ = "entity_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AnalyticsResult(Base):
    __tablename__ = "analytics_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_type: Mapped[str] = mapped_column(String(32), index=True)
    event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("events.id"), index=True, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_type: Mapped[str] = mapped_column(String(32), index=True)
    priority: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    message: Mapped[str] = mapped_column(String(512))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor: Mapped[str] = mapped_column(String(128), index=True)
    actor_role: Mapped[str] = mapped_column(String(32), index=True)
    service: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource: Mapped[str] = mapped_column(String(256), index=True)
    outcome: Mapped[str] = mapped_column(String(16), default="success", index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(64), index=True)
    model_family: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(24), default="trained", index=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    training_window_hours: Mapped[int] = mapped_column(Integer, default=24)
    created_by: Mapped[str] = mapped_column(String(128), default="system")
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "source_type": event.source_type,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "received_at": event.received_at.isoformat() if event.received_at else None,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "plate_text": event.plate_text,
        "device_id": event.device_id,
        "severity": event.severity,
        "metadata": event.meta or {},
        "payload": event.raw_payload or {},
    }


def get_entity_by_type_and_label(db: Session, entity_type: str, label: str) -> Entity | None:
    stmt = select(Entity).where(Entity.entity_type == entity_type, Entity.label == label)
    return db.execute(stmt).scalar_one_or_none()


def audit_to_dict(item: AuditLog) -> dict[str, Any]:
    return {
        "id": item.id,
        "actor": item.actor,
        "actor_role": item.actor_role,
        "service": item.service,
        "action": item.action,
        "resource": item.resource,
        "outcome": item.outcome,
        "details": item.details or {},
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def model_registry_to_dict(item: ModelRegistry, include_artifacts: bool = False) -> dict[str, Any]:
    body = {
        "id": item.id,
        "model_name": item.model_name,
        "model_family": item.model_family,
        "version": item.version,
        "status": item.status,
        "metrics": item.metrics or {},
        "config": item.config or {},
        "training_window_hours": item.training_window_hours,
        "created_by": item.created_by,
        "trained_at": item.trained_at.isoformat() if item.trained_at else None,
        "deployed_at": item.deployed_at.isoformat() if item.deployed_at else None,
    }
    if include_artifacts:
        body["artifacts"] = item.artifacts or {}
    return body
