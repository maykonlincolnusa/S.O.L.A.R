from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from shared.analytics_engine import (
    cluster_events,
    deep_risk_assessment,
    detect_anomalies,
    detect_patterns,
    ml_risk_assessment,
    predict_risk,
)
from shared.solar_common import AnalyticsResult, Event, ModelRegistry, get_db, model_registry_to_dict

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrainModelsPayload(BaseModel):
    hours: int = Field(default=168, ge=24, le=2160)
    ml_epochs: int = Field(default=160, ge=20, le=5000)
    ml_learning_rate: float = Field(default=0.08, gt=0.0001, le=1.0)
    deep_epochs: int = Field(default=220, ge=20, le=5000)
    deep_learning_rate: float = Field(default=0.03, gt=0.0001, le=1.0)
    deep_hidden_dim: int = Field(default=8, ge=2, le=256)
    deploy_after_train: bool = False
    created_by: str = Field(default="analytics-operator", min_length=2, max_length=128)


def load_recent_events(db: Session, hours: int) -> list[Event]:
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = select(Event).where(Event.occurred_at >= start).order_by(desc(Event.occurred_at))
    return list(db.execute(stmt).scalars().all())


def persist_result(
    db: Session,
    analysis_type: str,
    details: dict[str, Any],
    score: float | None = None,
    event_id: str | None = None,
) -> None:
    row = AnalyticsResult(
        analysis_type=analysis_type,
        score=score,
        event_id=event_id,
        details=details,
    )
    db.add(row)


def next_model_version(db: Session, model_name: str) -> int:
    stmt = select(ModelRegistry).where(ModelRegistry.model_name == model_name).order_by(desc(ModelRegistry.version))
    latest = db.execute(stmt).scalars().first()
    if not latest:
        return 1
    return int(latest.version) + 1


def mark_only_model_deployed(db: Session, model_name: str, deployed_id: str) -> None:
    stmt = select(ModelRegistry).where(ModelRegistry.model_name == model_name)
    rows = list(db.execute(stmt).scalars().all())
    for row in rows:
        if row.id == deployed_id:
            row.status = "deployed"
            row.deployed_at = datetime.now(timezone.utc)
        elif row.status == "deployed":
            row.status = "trained"


@router.post("/models/train")
def train_models(payload: TrainModelsPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    events = load_recent_events(db, hours=payload.hours)
    if len(events) < 10:
        raise HTTPException(status_code=400, detail="Not enough events to train models. Need at least 10.")

    ml_result = ml_risk_assessment(
        events,
        epochs=payload.ml_epochs,
        learning_rate=payload.ml_learning_rate,
        include_artifacts=True,
    )
    deep_result = deep_risk_assessment(
        events,
        epochs=payload.deep_epochs,
        learning_rate=payload.deep_learning_rate,
        hidden_dim=payload.deep_hidden_dim,
        include_artifacts=True,
    )

    ml_row = ModelRegistry(
        model_name="risk_ml_logistic",
        model_family="ml",
        version=next_model_version(db, "risk_ml_logistic"),
        status="trained",
        metrics=ml_result.get("metrics", {}),
        config={
            "hours": payload.hours,
            "epochs": payload.ml_epochs,
            "learning_rate": payload.ml_learning_rate,
            "algorithm": "logistic_regression",
        },
        artifacts=ml_result.get("artifacts", {}),
        training_window_hours=payload.hours,
        created_by=payload.created_by,
    )
    db.add(ml_row)
    db.flush()

    deep_row = ModelRegistry(
        model_name="risk_deep_mlp",
        model_family="deep_learning",
        version=next_model_version(db, "risk_deep_mlp"),
        status="trained",
        metrics=deep_result.get("metrics", {}),
        config={
            "hours": payload.hours,
            "epochs": payload.deep_epochs,
            "learning_rate": payload.deep_learning_rate,
            "hidden_dim": payload.deep_hidden_dim,
            "algorithm": "mlp_binary_classifier",
        },
        artifacts=deep_result.get("artifacts", {}),
        training_window_hours=payload.hours,
        created_by=payload.created_by,
    )
    db.add(deep_row)
    db.flush()

    if payload.deploy_after_train:
        mark_only_model_deployed(db, "risk_ml_logistic", ml_row.id)
        mark_only_model_deployed(db, "risk_deep_mlp", deep_row.id)

    persist_result(
        db,
        analysis_type="model_training",
        score=None,
        details={
            "hours": payload.hours,
            "created_by": payload.created_by,
            "deploy_after_train": payload.deploy_after_train,
            "trained_models": [
                {"id": ml_row.id, "name": ml_row.model_name, "version": ml_row.version},
                {"id": deep_row.id, "name": deep_row.model_name, "version": deep_row.version},
            ],
        },
    )

    db.commit()
    db.refresh(ml_row)
    db.refresh(deep_row)

    return {
        "status": "ok",
        "trained_models": [model_registry_to_dict(ml_row), model_registry_to_dict(deep_row)],
        "ml_score": ml_result.get("score"),
        "deep_score": deep_result.get("score"),
    }


@router.get("/models/registry")
def list_model_registry(
    model_name: str | None = None,
    status: str | None = Query(default=None, pattern="^(trained|deployed|archived)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    include_artifacts: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(ModelRegistry).order_by(desc(ModelRegistry.trained_at)).limit(limit)
    if model_name and status:
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.model_name == model_name, ModelRegistry.status == status)
            .order_by(desc(ModelRegistry.trained_at))
            .limit(limit)
        )
    elif model_name:
        stmt = select(ModelRegistry).where(ModelRegistry.model_name == model_name).order_by(desc(ModelRegistry.trained_at)).limit(limit)
    elif status:
        stmt = select(ModelRegistry).where(ModelRegistry.status == status).order_by(desc(ModelRegistry.trained_at)).limit(limit)

    rows = list(db.execute(stmt).scalars().all())
    return {
        "count": len(rows),
        "models": [model_registry_to_dict(row, include_artifacts=include_artifacts) for row in rows],
    }


@router.patch("/models/{model_id}/deploy")
def deploy_model(model_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(ModelRegistry, model_id)
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    mark_only_model_deployed(db, row.model_name, row.id)
    db.commit()
    db.refresh(row)
    return {"status": "deployed", "model": model_registry_to_dict(row)}


@router.get("/models/deployed")
def list_deployed_models(db: Session = Depends(get_db)) -> dict[str, Any]:
    stmt = select(ModelRegistry).where(ModelRegistry.status == "deployed").order_by(desc(ModelRegistry.trained_at))
    rows = list(db.execute(stmt).scalars().all())
    latest_by_name: dict[str, ModelRegistry] = {}
    for row in rows:
        existing = latest_by_name.get(row.model_name)
        if not existing or row.version > existing.version:
            latest_by_name[row.model_name] = row
    selected = list(latest_by_name.values())
    selected.sort(key=lambda item: item.model_name)
    return {"count": len(selected), "models": [model_registry_to_dict(row) for row in selected]}


@router.get("/patterns")
def patterns(hours: int = Query(default=24, ge=1, le=720), db: Session = Depends(get_db)) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    results = detect_patterns(events)
    for row in results:
        persist_result(db, analysis_type="pattern", score=row.get("score"), details=row)
    db.commit()
    return {"count": len(results), "patterns": results}


@router.get("/risk")
def risk(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    result = predict_risk(events, focus_lat=lat, focus_lon=lon)
    persist_result(db, analysis_type="risk", score=result["score"], details=result)
    db.commit()
    return result


@router.get("/ml/risk")
def ml_risk(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    result = ml_risk_assessment(events, focus_lat=lat, focus_lon=lon)
    persist_result(db, analysis_type="ml_risk", score=result.get("score"), details=result)
    db.commit()
    return result


@router.get("/deep/risk")
def deep_risk(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    result = deep_risk_assessment(events, focus_lat=lat, focus_lon=lon)
    persist_result(db, analysis_type="deep_risk", score=result.get("score"), details=result)
    db.commit()
    return result


@router.get("/models/compare")
def compare_models(
    hours: int = Query(default=24, ge=1, le=720),
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    rule_based = predict_risk(events, focus_lat=lat, focus_lon=lon)
    ml = ml_risk_assessment(events, focus_lat=lat, focus_lon=lon)
    deep = deep_risk_assessment(events, focus_lat=lat, focus_lon=lon)
    combined_score = round(float(np.mean([rule_based["score"], ml["score"], deep["score"]])), 3)
    combined_label = "high" if combined_score >= 0.75 else "medium" if combined_score >= 0.45 else "low"
    result = {
        "ensemble": {"score": combined_score, "label": combined_label},
        "rule_based": rule_based,
        "ml": ml,
        "deep_learning": deep,
    }
    persist_result(db, analysis_type="model_compare", score=combined_score, details=result)
    db.commit()
    return result


@router.get("/clusters")
def clusters(
    hours: int = Query(default=24, ge=1, le=720),
    precision: int = Query(default=2, ge=1, le=4),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    results = cluster_events(events, precision=precision)
    for row in results:
        persist_result(db, analysis_type="cluster", score=row.get("score"), details=row)
    db.commit()
    return {"count": len(results), "clusters": results}


@router.get("/anomalies")
def anomalies(
    hours: int = Query(default=24, ge=1, le=720),
    zscore_threshold: float = Query(default=2.2, ge=1.0, le=5.0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = load_recent_events(db, hours=hours)
    results = detect_anomalies(events, zscore_threshold=zscore_threshold)
    for row in results:
        persist_result(
            db,
            analysis_type="anomaly",
            score=row.get("score"),
            details=row,
            event_id=row.get("event_id"),
        )
    db.commit()
    return {"count": len(results), "anomalies": results}


@router.get("/realtime/signals")
def realtime_signals(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = (
        select(AnalyticsResult)
        .where(AnalyticsResult.analysis_type.in_(["stream_risk_signal", "stream_anomaly_signal"]))
        .order_by(desc(AnalyticsResult.created_at))
        .limit(limit)
    )
    rows = list(db.execute(stmt).scalars().all())
    return {
        "count": len(rows),
        "signals": [
            {
                "id": row.id,
                "analysis_type": row.analysis_type,
                "event_id": row.event_id,
                "score": row.score,
                "details": row.details or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }
