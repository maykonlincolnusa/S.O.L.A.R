from __future__ import annotations

import os

import httpx

API_BASE = os.getenv("SOLAR_API_BASE", "http://localhost:8080/api")
API_KEY = os.getenv("SOLAR_TRAIN_API_KEY", "dev-admin-key")


def main() -> None:
    payload = {
        "hours": int(os.getenv("SOLAR_TRAIN_HOURS", "168")),
        "ml_epochs": int(os.getenv("SOLAR_ML_EPOCHS", "180")),
        "ml_learning_rate": float(os.getenv("SOLAR_ML_LR", "0.08")),
        "deep_epochs": int(os.getenv("SOLAR_DEEP_EPOCHS", "260")),
        "deep_learning_rate": float(os.getenv("SOLAR_DEEP_LR", "0.03")),
        "deep_hidden_dim": int(os.getenv("SOLAR_DEEP_HIDDEN", "10")),
        "deploy_after_train": os.getenv("SOLAR_DEPLOY_AFTER_TRAIN", "true").lower() in {"1", "true", "yes"},
        "created_by": os.getenv("SOLAR_CREATED_BY", "cli-trainer"),
    }

    with httpx.Client(timeout=60.0, headers={"X-API-Key": API_KEY}) as client:
        response = client.post(f"{API_BASE}/analytics/models/train", json=payload)
        response.raise_for_status()
        body = response.json()
        print("Training completed.")
        print(f"ML score snapshot: {body.get('ml_score')}")
        print(f"Deep score snapshot: {body.get('deep_score')}")
        print("Trained models:")
        for item in body.get("trained_models", []):
            print(f"- {item.get('model_name')} v{item.get('version')} status={item.get('status')}")


if __name__ == "__main__":
    main()

