from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from shared.solar_common import Entity, EntityRelation, Event, event_to_dict, get_db, get_entity_by_type_and_label

router = APIRouter(prefix="/semantic", tags=["semantic"])


class EntityPayload(BaseModel):
    entity_type: str = Field(min_length=2, max_length=32)
    label: str = Field(min_length=1, max_length=128)
    attributes: dict[str, Any] = Field(default_factory=dict)


class RelationPayload(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: str = Field(min_length=2, max_length=64)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


@router.post("/entities")
def upsert_entity(payload: EntityPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    existing = get_entity_by_type_and_label(db, payload.entity_type, payload.label)
    if existing:
        merged = dict(existing.attributes or {})
        merged.update(payload.attributes)
        existing.attributes = merged
        db.commit()
        db.refresh(existing)
        return {"status": "updated", "entity": entity_to_dict(existing)}

    entity = Entity(entity_type=payload.entity_type, label=payload.label, attributes=payload.attributes)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return {"status": "created", "entity": entity_to_dict(entity)}


@router.post("/relations")
def create_relation(payload: RelationPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    source = db.get(Entity, payload.source_entity_id)
    target = db.get(Entity, payload.target_entity_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Source or target entity not found")

    relation = EntityRelation(
        source_entity_id=payload.source_entity_id,
        target_entity_id=payload.target_entity_id,
        relation_type=payload.relation_type,
        confidence=payload.confidence,
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return {"status": "linked", "relation": relation_to_dict(relation)}


@router.get("/context/{entity_id}")
def context(entity_id: str, event_limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> dict[str, Any]:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    relations_stmt = select(EntityRelation).where(
        or_(
            EntityRelation.source_entity_id == entity_id,
            EntityRelation.target_entity_id == entity_id,
        )
    )
    relations = list(db.execute(relations_stmt).scalars().all())

    attributes = entity.attributes or {}
    events: list[Event] = []
    if attributes.get("plate_text"):
        events_stmt = select(Event).where(Event.plate_text == attributes["plate_text"]).limit(event_limit)
        events.extend(db.execute(events_stmt).scalars().all())
    if attributes.get("device_id"):
        events_stmt = select(Event).where(Event.device_id == attributes["device_id"]).limit(event_limit)
        events.extend(db.execute(events_stmt).scalars().all())

    dedup_events = {event.id: event for event in events}
    return {
        "entity": entity_to_dict(entity),
        "relations": [relation_to_dict(rel) for rel in relations],
        "events": [event_to_dict(item) for item in dedup_events.values()],
    }


@router.get("/graph")
def graph(limit: int = Query(default=200, ge=1, le=2000), db: Session = Depends(get_db)) -> dict[str, Any]:
    entities_stmt = select(Entity).limit(limit)
    relations_stmt = select(EntityRelation).limit(limit)
    entities = db.execute(entities_stmt).scalars().all()
    relations = db.execute(relations_stmt).scalars().all()
    return {
        "nodes": [entity_to_dict(entity) for entity in entities],
        "edges": [relation_to_dict(relation) for relation in relations],
    }


def entity_to_dict(entity: Entity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "entity_type": entity.entity_type,
        "label": entity.label,
        "attributes": entity.attributes or {},
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
    }


def relation_to_dict(relation: EntityRelation) -> dict[str, Any]:
    return {
        "id": relation.id,
        "source_entity_id": relation.source_entity_id,
        "target_entity_id": relation.target_entity_id,
        "relation_type": relation.relation_type,
        "confidence": relation.confidence,
        "created_at": relation.created_at.isoformat() if relation.created_at else None,
    }

