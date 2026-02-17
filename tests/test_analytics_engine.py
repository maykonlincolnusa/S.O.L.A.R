from datetime import datetime, timedelta, timezone

from shared.analytics_engine import (
    cluster_events,
    deep_risk_assessment,
    detect_anomalies,
    detect_patterns,
    ml_risk_assessment,
    predict_risk,
)


def _event(idx: int, lat: float, lon: float, severity: int, plate: str | None = None):
    return {
        "id": f"e-{idx}",
        "occurred_at": (datetime.now(timezone.utc) - timedelta(minutes=idx)).isoformat(),
        "latitude": lat,
        "longitude": lon,
        "severity": severity,
        "plate_text": plate,
        "source_type": "camera",
    }


def test_cluster_events_returns_clusters():
    events = [
        _event(1, -23.55, -46.63, 2),
        _event(2, -23.551, -46.631, 3),
        _event(3, -23.70, -46.80, 1),
    ]
    clusters = cluster_events(events, precision=2, min_cluster_size=2)
    assert clusters
    assert clusters[0]["count"] >= 2


def test_detect_patterns_finds_repeated_plate():
    events = [
        _event(1, -23.55, -46.63, 2, plate="SOL1234"),
        _event(2, -23.60, -46.70, 3, plate="SOL1234"),
        _event(3, -23.56, -46.66, 4, plate="SOL1234"),
    ]
    patterns = detect_patterns(events)
    assert patterns
    assert patterns[0]["plate_text"] == "SOL1234"


def test_predict_risk_returns_bounded_score():
    events = [_event(i, -23.55 + i * 0.001, -46.63 + i * 0.001, 3) for i in range(1, 10)]
    risk = predict_risk(events, focus_lat=-23.55, focus_lon=-46.63)
    assert 0.0 <= risk["score"] <= 1.0


def test_detect_anomalies_flags_high_severity_outlier():
    events = [
        _event(1, -23.55, -46.63, 1),
        _event(2, -23.551, -46.631, 1),
        _event(3, -23.552, -46.632, 5),
        _event(4, -23.553, -46.633, 1),
    ]
    anomalies = detect_anomalies(events, zscore_threshold=1.5)
    assert anomalies


def test_ml_risk_assessment_returns_bounded_score():
    events = [_event(i, -23.55 + i * 0.001, -46.63 + i * 0.001, (i % 5) + 1) for i in range(1, 60)]
    result = ml_risk_assessment(events, focus_lat=-23.55, focus_lon=-46.63)
    assert 0.0 <= result["score"] <= 1.0
    assert result["label"] in {"low", "medium", "high"}


def test_deep_risk_assessment_returns_bounded_score():
    events = [_event(i, -23.55 + i * 0.001, -46.63 + i * 0.001, (i % 5) + 1) for i in range(1, 80)]
    result = deep_risk_assessment(events, focus_lat=-23.55, focus_lon=-46.63)
    assert 0.0 <= result["score"] <= 1.0
    assert result["label"] in {"low", "medium", "high"}
