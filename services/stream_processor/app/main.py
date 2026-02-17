from __future__ import annotations

import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from threading import Event as ThreadEvent
from threading import Thread
from typing import Any

from fastapi import FastAPI, Query
from sqlalchemy import desc, select

from shared.analytics_engine import detect_anomalies, predict_risk
from shared.solar_common import Alert, AnalyticsResult, SessionLocal, init_db
from shared.streaming import STREAM_NAME, get_redis_client

STREAM_RISK_THRESHOLD = float(os.getenv("STREAM_SIGNAL_RISK_THRESHOLD", "0.8"))
STREAM_ANOMALY_THRESHOLD = float(os.getenv("STREAM_SIGNAL_ANOMALY_THRESHOLD", "0.8"))
WINDOW_SIZE = int(os.getenv("STREAM_WINDOW_SIZE", "240"))

app = FastAPI(title="SOLAR Stream Processor", version="1.0.0")
stop_event = ThreadEvent()
stream_window: deque[dict[str, Any]] = deque(maxlen=WINDOW_SIZE)

state: dict[str, Any] = {
    "connected": False,
    "stream": STREAM_NAME,
    "last_id": os.getenv("STREAM_START_ID", "$"),
    "processed": 0,
    "last_processed_at": None,
    "last_error": None,
}

worker_thread: Thread | None = None


def _create_alert(db, *, alert_type: str, priority: str, message: str, details: dict[str, Any]) -> None:
    status = "pending_approval" if priority == "high" else "open"
    db.add(
        Alert(
            alert_type=alert_type,
            priority=priority,
            status=status,
            message=message,
            details=details,
        )
    )


def _persist_signal(event: dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        stream_window.append(event)
        risk = predict_risk(stream_window)
        db.add(
            AnalyticsResult(
                analysis_type="stream_risk_signal",
                event_id=event.get("id"),
                score=risk.get("score"),
                details={"risk": risk, "event": event},
            )
        )

        if float(risk.get("score", 0)) >= STREAM_RISK_THRESHOLD:
            priority = "high" if float(risk.get("score", 0)) >= 0.9 else "medium"
            _create_alert(
                db,
                alert_type="stream_signal",
                priority=priority,
                message=f"Real-time risk signal on event {event.get('id')}",
                details={"risk": risk, "event": event, "source": "stream_processor"},
            )

        anomalies = detect_anomalies(stream_window, zscore_threshold=2.2)
        if anomalies:
            top = anomalies[0]
            score = float(top.get("score", 0))
            if score >= STREAM_ANOMALY_THRESHOLD and top.get("event_id") == event.get("id"):
                priority = "high" if score >= 0.9 else "medium"
                db.add(
                    AnalyticsResult(
                        analysis_type="stream_anomaly_signal",
                        event_id=event.get("id"),
                        score=score,
                        details={"anomaly": top, "event": event},
                    )
                )
                _create_alert(
                    db,
                    alert_type="stream_anomaly",
                    priority=priority,
                    message=f"Real-time anomaly signal on event {event.get('id')}",
                    details={"anomaly": top, "event": event, "source": "stream_processor"},
                )

        db.commit()
        state["processed"] += 1
        state["last_processed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:
        db.rollback()
        state["last_error"] = str(exc)
    finally:
        db.close()


def _consume_forever() -> None:
    last_id = state["last_id"]
    while not stop_event.is_set():
        client = get_redis_client()
        if client is None:
            state["connected"] = False
            state["last_error"] = "redis client unavailable"
            time.sleep(2)
            continue

        try:
            messages = client.xread({STREAM_NAME: last_id}, count=20, block=5000)
            state["connected"] = True
            if not messages:
                continue
            for _, entries in messages:
                for entry_id, fields in entries:
                    raw_event = fields.get("event")
                    if not raw_event:
                        last_id = entry_id
                        state["last_id"] = last_id
                        continue
                    event = json.loads(raw_event)
                    _persist_signal(event)
                    last_id = entry_id
                    state["last_id"] = last_id
        except Exception as exc:
            state["connected"] = False
            state["last_error"] = str(exc)
            time.sleep(2)


@app.on_event("startup")
def startup() -> None:
    global worker_thread
    init_db()
    stop_event.clear()
    worker_thread = Thread(target=_consume_forever, daemon=True)
    worker_thread.start()


@app.on_event("shutdown")
def shutdown() -> None:
    stop_event.set()
    if worker_thread and worker_thread.is_alive():
        worker_thread.join(timeout=2)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "stream_processor", **state}


@app.get("/stream/signals")
def stream_signals(limit: int = Query(default=100, ge=1, le=1000)) -> dict[str, Any]:
    db = SessionLocal()
    try:
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
    finally:
        db.close()

