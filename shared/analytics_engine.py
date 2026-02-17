from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np


def _safe_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _as_dict(event: Any) -> dict[str, Any]:
    if isinstance(event, dict):
        data = event.copy()
    else:
        data = {
            "id": getattr(event, "id", None),
            "occurred_at": getattr(event, "occurred_at", None),
            "latitude": getattr(event, "latitude", None),
            "longitude": getattr(event, "longitude", None),
            "plate_text": getattr(event, "plate_text", None),
            "device_id": getattr(event, "device_id", None),
            "severity": getattr(event, "severity", 1),
            "source_type": getattr(event, "source_type", "unknown"),
            "metadata": getattr(event, "meta", {}) or {},
        }

    data["occurred_at"] = _safe_datetime(data.get("occurred_at"))
    if data.get("severity") is None:
        data["severity"] = 1
    return data


def normalize_events(events: Iterable[Any]) -> list[dict[str, Any]]:
    normalized = [_as_dict(e) for e in events]
    return [e for e in normalized if e.get("occurred_at") is not None]


def detect_patterns(events: Iterable[Any]) -> list[dict[str, Any]]:
    data = normalize_events(events)
    by_plate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in data:
        plate = event.get("plate_text")
        if plate:
            by_plate[plate].append(event)

    patterns: list[dict[str, Any]] = []
    for plate, entries in by_plate.items():
        unique_cells = set()
        severities = []
        sources = Counter()

        for entry in entries:
            if entry.get("latitude") is not None and entry.get("longitude") is not None:
                unique_cells.add((round(entry["latitude"], 2), round(entry["longitude"], 2)))
            severities.append(int(entry.get("severity", 1)))
            sources.update([entry.get("source_type", "unknown")])

        if len(entries) >= 3 and len(unique_cells) >= 2:
            avg_severity = float(np.mean(severities)) if severities else 1.0
            score = min(1.0, 0.2 * len(entries) + 0.15 * len(unique_cells) + 0.1 * avg_severity)
            patterns.append(
                {
                    "pattern": "repeated_vehicle_movement",
                    "plate_text": plate,
                    "event_count": len(entries),
                    "zones": len(unique_cells),
                    "score": round(score, 3),
                    "top_source": sources.most_common(1)[0][0] if sources else "unknown",
                }
            )

    patterns.sort(key=lambda item: item["score"], reverse=True)
    return patterns


def cluster_events(events: Iterable[Any], precision: int = 2, min_cluster_size: int = 2) -> list[dict[str, Any]]:
    data = normalize_events(events)
    buckets: dict[tuple[float, float], list[dict[str, Any]]] = defaultdict(list)

    for event in data:
        lat = event.get("latitude")
        lon = event.get("longitude")
        if lat is None or lon is None:
            continue
        key = (round(float(lat), precision), round(float(lon), precision))
        buckets[key].append(event)

    clusters = []
    for (lat, lon), entries in buckets.items():
        if len(entries) < min_cluster_size:
            continue
        avg_severity = float(np.mean([int(e.get("severity", 1)) for e in entries]))
        clusters.append(
            {
                "center": {"latitude": lat, "longitude": lon},
                "count": len(entries),
                "avg_severity": round(avg_severity, 2),
                "score": round(min(1.0, 0.12 * len(entries) + 0.1 * avg_severity), 3),
            }
        )

    clusters.sort(key=lambda item: item["count"], reverse=True)
    return clusters


def predict_risk(
    events: Iterable[Any],
    focus_lat: float | None = None,
    focus_lon: float | None = None,
) -> dict[str, Any]:
    data = normalize_events(events)
    if not data:
        return {
            "score": 0.0,
            "factors": {"density": 0.0, "severity": 0.0, "recency": 0.0, "focus_proximity": 0.0},
            "label": "low",
        }

    now = datetime.now(timezone.utc)
    event_count = len(data)
    avg_severity = float(np.mean([int(e.get("severity", 1)) for e in data]))
    latest_event_time = max(e["occurred_at"] for e in data if e.get("occurred_at"))
    minutes_since_last = max(1.0, (now - latest_event_time).total_seconds() / 60.0)

    density_factor = min(1.0, event_count / 60.0)
    severity_factor = min(1.0, avg_severity / 5.0)
    recency_factor = min(1.0, 90.0 / minutes_since_last)

    proximity_factor = 0.4
    if focus_lat is not None and focus_lon is not None:
        distances = []
        for event in data:
            lat = event.get("latitude")
            lon = event.get("longitude")
            if lat is None or lon is None:
                continue
            distances.append(haversine_km(focus_lat, focus_lon, float(lat), float(lon)))

        if distances:
            nearest_km = min(distances)
            proximity_factor = max(0.0, min(1.0, 1 - (nearest_km / 15.0)))
        else:
            proximity_factor = 0.1

    score = (
        0.35 * density_factor
        + 0.30 * severity_factor
        + 0.20 * recency_factor
        + 0.15 * proximity_factor
    )
    score = float(max(0.0, min(1.0, score)))

    if score >= 0.75:
        label = "high"
    elif score >= 0.45:
        label = "medium"
    else:
        label = "low"

    return {
        "score": round(score, 3),
        "label": label,
        "factors": {
            "density": round(density_factor, 3),
            "severity": round(severity_factor, 3),
            "recency": round(recency_factor, 3),
            "focus_proximity": round(proximity_factor, 3),
        },
    }


def detect_anomalies(events: Iterable[Any], zscore_threshold: float = 2.2) -> list[dict[str, Any]]:
    data = normalize_events(events)
    if len(data) < 3:
        return []

    severities = np.array([int(e.get("severity", 1)) for e in data], dtype=float)
    mean = float(np.mean(severities))
    std = float(np.std(severities))
    std = std if std > 0 else 1.0

    anomalies: list[dict[str, Any]] = []
    for event in data:
        severity = float(int(event.get("severity", 1)))
        zscore = abs((severity - mean) / std)
        isolated_geo = is_geo_isolated(event, data)
        if zscore >= zscore_threshold or (severity >= 4 and isolated_geo):
            score = min(1.0, 0.35 * zscore + (0.3 if isolated_geo else 0.0) + 0.1 * severity)
            anomalies.append(
                {
                    "event_id": event.get("id"),
                    "reason": "severity_outlier" if zscore >= zscore_threshold else "geo_isolation",
                    "severity": int(severity),
                    "zscore": round(float(zscore), 3),
                    "score": round(float(score), 3),
                    "location": {"latitude": event.get("latitude"), "longitude": event.get("longitude")},
                }
            )

    anomalies.sort(key=lambda item: item["score"], reverse=True)
    return anomalies


def is_geo_isolated(event: dict[str, Any], population: list[dict[str, Any]], threshold_km: float = 3.0) -> bool:
    lat = event.get("latitude")
    lon = event.get("longitude")
    if lat is None or lon is None:
        return False

    close_neighbors = 0
    for peer in population:
        if peer.get("id") == event.get("id"):
            continue
        peer_lat = peer.get("latitude")
        peer_lon = peer.get("longitude")
        if peer_lat is None or peer_lon is None:
            continue
        dist = haversine_km(float(lat), float(lon), float(peer_lat), float(peer_lon))
        if dist <= threshold_km:
            close_neighbors += 1
            if close_neighbors >= 2:
                return False
    return True


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def ml_risk_assessment(
    events: Iterable[Any],
    focus_lat: float | None = None,
    focus_lon: float | None = None,
    epochs: int = 160,
    learning_rate: float = 0.08,
    include_artifacts: bool = False,
) -> dict[str, Any]:
    data = normalize_events(events)
    if len(data) < 10:
        fallback = predict_risk(data, focus_lat=focus_lat, focus_lon=focus_lon)
        return {
            "score": fallback["score"],
            "label": fallback["label"],
            "model": "ml_logistic_regression_fallback",
            "reason": "insufficient_events_for_training",
            "training_samples": len(data),
            "metrics": {},
            "top_feature_importance": [],
        }

    x_raw, y, feature_names = _build_ml_dataset(data, focus_lat=focus_lat, focus_lon=focus_lon)
    x, mean, std = _standardize_matrix(x_raw)

    train_x, train_y, test_x, test_y = _train_test_split(x, y, ratio=0.8)
    weights, bias = _train_logistic_regression(train_x, train_y, epochs=epochs, learning_rate=learning_rate)

    latest_index = int(np.argmax([item["occurred_at"].timestamp() for item in data]))
    latest_vec = x[latest_index]
    latest_prob = float(_sigmoid(np.dot(latest_vec, weights) + bias))

    test_probs = _sigmoid(test_x @ weights + bias)
    metrics = _classification_metrics(test_y, test_probs, threshold=0.5)

    label = _risk_label_from_score(latest_prob)
    feature_importance = sorted(
        zip(feature_names, np.abs(weights).tolist()),
        key=lambda item: item[1],
        reverse=True,
    )[:5]

    result: dict[str, Any] = {
        "score": round(latest_prob, 3),
        "label": label,
        "model": "ml_logistic_regression",
        "training_samples": int(len(train_x)),
        "test_samples": int(len(test_x)),
        "metrics": metrics,
        "top_feature_importance": [
            {"feature": name, "weight_abs": round(float(weight), 4)} for name, weight in feature_importance
        ],
        "latest_event_id": data[latest_index].get("id"),
    }
    if include_artifacts:
        result["artifacts"] = {
            "feature_names": feature_names,
            "standardization": {"mean": mean.tolist(), "std": std.tolist()},
            "weights": weights.tolist(),
            "bias": float(bias),
            "hyperparameters": {"epochs": epochs, "learning_rate": learning_rate, "algorithm": "logistic_regression"},
        }
    return result


def deep_risk_assessment(
    events: Iterable[Any],
    focus_lat: float | None = None,
    focus_lon: float | None = None,
    epochs: int = 220,
    learning_rate: float = 0.03,
    hidden_dim: int = 8,
    include_artifacts: bool = False,
) -> dict[str, Any]:
    data = normalize_events(events)
    if len(data) < 20:
        fallback = ml_risk_assessment(data, focus_lat=focus_lat, focus_lon=focus_lon)
        fallback["model"] = "deep_mlp_fallback_to_ml"
        fallback["reason"] = "insufficient_events_for_deep_learning"
        return fallback

    x_raw, y, feature_names = _build_ml_dataset(data, focus_lat=focus_lat, focus_lon=focus_lon)
    x, mean, std = _standardize_matrix(x_raw)
    train_x, train_y, test_x, test_y = _train_test_split(x, y, ratio=0.8)

    params = _train_mlp_binary_classifier(
        train_x,
        train_y,
        hidden_dim=hidden_dim,
        epochs=epochs,
        learning_rate=learning_rate,
    )

    latest_index = int(np.argmax([item["occurred_at"].timestamp() for item in data]))
    latest_vec = x[latest_index : latest_index + 1]
    latest_prob = float(_mlp_predict_proba(latest_vec, params)[0])

    test_probs = _mlp_predict_proba(test_x, params)
    metrics = _classification_metrics(test_y, test_probs, threshold=0.5)
    label = _risk_label_from_score(latest_prob)

    w1 = params["w1"]
    importance = np.mean(np.abs(w1), axis=1)
    top_features = sorted(zip(feature_names, importance.tolist()), key=lambda item: item[1], reverse=True)[:5]

    result: dict[str, Any] = {
        "score": round(latest_prob, 3),
        "label": label,
        "model": "deep_mlp_binary_classifier",
        "training_samples": int(len(train_x)),
        "test_samples": int(len(test_x)),
        "metrics": metrics,
        "top_feature_importance": [
            {"feature": name, "weight_abs": round(float(weight), 4)} for name, weight in top_features
        ],
        "latest_event_id": data[latest_index].get("id"),
    }
    if include_artifacts:
        result["artifacts"] = {
            "feature_names": feature_names,
            "standardization": {"mean": mean.tolist(), "std": std.tolist()},
            "weights": {
                "w1": params["w1"].tolist(),
                "b1": params["b1"].tolist(),
                "w2": params["w2"].tolist(),
                "b2": params["b2"].tolist(),
            },
            "hyperparameters": {
                "epochs": epochs,
                "learning_rate": learning_rate,
                "hidden_dim": hidden_dim,
                "algorithm": "mlp_binary_classifier",
            },
        }
    return result


def _build_ml_dataset(
    events: list[dict[str, Any]],
    focus_lat: float | None = None,
    focus_lon: float | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    now = datetime.now(timezone.utc)
    source_types = sorted({event.get("source_type", "unknown") for event in events})
    source_index = {source: idx for idx, source in enumerate(source_types)}

    base_feature_names = [
        "severity_scaled",
        "has_plate",
        "has_device",
        "has_geo",
        "minutes_since_event_scaled",
        "distance_to_focus_scaled",
        "hour_of_day_scaled",
    ]
    source_feature_names = [f"source_is_{source}" for source in source_types]
    feature_names = base_feature_names + source_feature_names

    x_rows: list[list[float]] = []
    y_rows: list[float] = []

    for event in events:
        occurred_at = event.get("occurred_at") or now
        minutes_since = max(0.0, (now - occurred_at).total_seconds() / 60.0)
        severity = float(int(event.get("severity", 1)))
        has_plate = 1.0 if event.get("plate_text") else 0.0
        has_device = 1.0 if event.get("device_id") else 0.0
        has_geo = 1.0 if event.get("latitude") is not None and event.get("longitude") is not None else 0.0

        if (
            focus_lat is not None
            and focus_lon is not None
            and event.get("latitude") is not None
            and event.get("longitude") is not None
        ):
            distance = haversine_km(focus_lat, focus_lon, float(event["latitude"]), float(event["longitude"]))
        else:
            distance = 5.0

        hour = occurred_at.hour + (occurred_at.minute / 60.0)
        row = [
            min(1.0, severity / 5.0),
            has_plate,
            has_device,
            has_geo,
            min(1.0, minutes_since / 180.0),
            min(1.0, distance / 20.0),
            hour / 24.0,
        ]

        one_hot = [0.0] * len(source_types)
        one_hot[source_index[event.get("source_type", "unknown")]] = 1.0
        row.extend(one_hot)
        x_rows.append(row)

        y_rows.append(float(_weak_risk_label(event)))

    return np.array(x_rows, dtype=float), np.array(y_rows, dtype=float), feature_names


def _weak_risk_label(event: dict[str, Any]) -> int:
    severity = int(event.get("severity", 1))
    source_type = str(event.get("source_type", "unknown"))
    meta = event.get("metadata", {}) or {}

    if bool(meta.get("known_incident")):
        return 1
    if severity >= 4:
        return 1
    if source_type == "police_records" and severity >= 3:
        return 1
    if source_type == "plate_ocr" and severity >= 3:
        return 1
    return 0


def _standardize_matrix(
    x: np.ndarray,
    mean: np.ndarray | None = None,
    std: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    computed_mean = np.mean(x, axis=0) if mean is None else mean
    computed_std = np.std(x, axis=0) if std is None else std
    computed_std = np.where(computed_std == 0.0, 1.0, computed_std)
    return (x - computed_mean) / computed_std, computed_mean, computed_std


def _train_test_split(
    x: np.ndarray,
    y: np.ndarray,
    ratio: float = 0.8,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = len(x)
    if n <= 2:
        return x, y, x, y
    split = max(1, min(n - 1, int(n * ratio)))
    return x[:split], y[:split], x[split:], y[split:]


def _sigmoid(z: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40, 40)))


def _train_logistic_regression(
    x: np.ndarray,
    y: np.ndarray,
    epochs: int = 120,
    learning_rate: float = 0.05,
    l2: float = 0.0005,
) -> tuple[np.ndarray, float]:
    n_samples, n_features = x.shape
    weights = np.zeros(n_features, dtype=float)
    bias = 0.0

    for _ in range(max(10, epochs)):
        logits = x @ weights + bias
        probs = _sigmoid(logits)
        error = probs - y
        grad_w = (x.T @ error) / n_samples + l2 * weights
        grad_b = float(np.mean(error))

        weights -= learning_rate * grad_w
        bias -= learning_rate * grad_b

    return weights, bias


def _classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    if len(y_true) == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    y_pred = (y_prob >= threshold).astype(float)
    tp = float(np.sum((y_true == 1) & (y_pred == 1)))
    tn = float(np.sum((y_true == 0) & (y_pred == 0)))
    fp = float(np.sum((y_true == 0) & (y_pred == 1)))
    fn = float(np.sum((y_true == 1) & (y_pred == 0)))

    accuracy = (tp + tn) / max(1.0, tp + tn + fp + fn)
    precision = tp / max(1.0, tp + fp)
    recall = tp / max(1.0, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)

    return {
        "accuracy": round(float(accuracy), 3),
        "precision": round(float(precision), 3),
        "recall": round(float(recall), 3),
        "f1": round(float(f1), 3),
    }


def _risk_label_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, x)


def _train_mlp_binary_classifier(
    x: np.ndarray,
    y: np.ndarray,
    hidden_dim: int = 8,
    epochs: int = 180,
    learning_rate: float = 0.02,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    n_samples, n_features = x.shape

    w1 = rng.normal(0.0, 0.15, size=(n_features, hidden_dim))
    b1 = np.zeros(hidden_dim)
    w2 = rng.normal(0.0, 0.15, size=(hidden_dim, 1))
    b2 = np.zeros(1)

    y_col = y.reshape(-1, 1)
    for _ in range(max(40, epochs)):
        z1 = x @ w1 + b1
        a1 = _relu(z1)
        z2 = a1 @ w2 + b2
        y_hat = _sigmoid(z2)

        dz2 = y_hat - y_col
        dw2 = (a1.T @ dz2) / n_samples
        db2 = np.mean(dz2, axis=0)

        da1 = dz2 @ w2.T
        dz1 = da1 * (z1 > 0).astype(float)
        dw1 = (x.T @ dz1) / n_samples
        db1 = np.mean(dz1, axis=0)

        w2 -= learning_rate * dw2
        b2 -= learning_rate * db2
        w1 -= learning_rate * dw1
        b1 -= learning_rate * db1

    return {"w1": w1, "b1": b1, "w2": w2, "b2": b2}


def _mlp_predict_proba(x: np.ndarray, params: dict[str, np.ndarray]) -> np.ndarray:
    z1 = x @ params["w1"] + params["b1"]
    a1 = _relu(z1)
    z2 = a1 @ params["w2"] + params["b2"]
    y_hat = _sigmoid(z2).reshape(-1)
    return y_hat
