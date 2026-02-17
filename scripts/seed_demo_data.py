from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone

import httpx

API_BASE = "http://localhost:8080/api"
API_KEY = os.getenv("SOLAR_SEED_API_KEY", "dev-admin-key")
SOURCES = ["camera", "public_data", "police_records", "gps_tracking", "plate_ocr"]
BASE_LAT = -23.5505
BASE_LON = -46.6333


def random_event() -> tuple[str, dict]:
    source = random.choice(SOURCES)
    occurred_at = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 300))
    payload = {
        "occurred_at": occurred_at.isoformat(),
        "latitude": BASE_LAT + (random.random() - 0.5) * 0.3,
        "longitude": BASE_LON + (random.random() - 0.5) * 0.3,
        "severity": random.randint(1, 5),
        "plate_text": f"SOL{random.randint(1000, 9999)}" if random.random() > 0.4 else None,
        "device_id": f"dev-{random.randint(1, 30)}",
        "metadata": {"seed": True, "city": "Sao Paulo"},
        "payload": {"sample": "demo"},
    }
    return source, payload


def main(total: int = 180) -> None:
    print(f"Seeding {total} synthetic events into {API_BASE}")
    with httpx.Client(timeout=15.0, headers={"X-API-Key": API_KEY}) as client:
        success = 0
        for _ in range(total):
            source, payload = random_event()
            response = client.post(f"{API_BASE}/ingest/{source}", json=payload)
            if response.status_code < 300:
                success += 1
        print(f"Ingested {success}/{total} events")

        response = client.post(
            f"{API_BASE}/alerts/evaluate",
            json={"lookback_hours": 24, "risk_threshold": 0.6, "anomaly_threshold": 0.8, "pattern_threshold": 0.75},
        )
        if response.status_code < 300:
            body = response.json()
            print(f"Alerts created: {body.get('created_count')}")
        else:
            print(f"Alert evaluation failed: HTTP {response.status_code}")


if __name__ == "__main__":
    main()
