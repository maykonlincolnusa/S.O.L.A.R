from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, Header, HTTPException

ROLE_PERMISSIONS = {
    "admin": {"*"},
    "analyst": {
        "events.read",
        "analytics.read",
        "analytics.write",
        "alerts.read",
        "semantic.read",
        "map.read",
        "chat.query",
        "audit.read",
    },
    "operator": {
        "ingest.write",
        "events.read",
        "analytics.read",
        "analytics.write",
        "alerts.read",
        "alerts.write",
        "alerts.approve",
        "semantic.read",
        "semantic.write",
        "map.read",
        "chat.query",
    },
    "viewer": {
        "events.read",
        "analytics.read",
        "alerts.read",
        "semantic.read",
        "map.read",
        "chat.query",
    },
    "ingestion": {
        "ingest.write",
        "events.read",
    },
    "compliance": {
        "compliance.write",
        "alerts.approve",
        "alerts.read",
        "audit.read",
    },
}


@dataclass
class Principal:
    actor: str
    role: str
    token_hint: str

    @property
    def permissions(self) -> set[str]:
        return ROLE_PERMISSIONS.get(self.role, set())

    def can(self, permission: str) -> bool:
        perms = self.permissions
        return "*" in perms or permission in perms


def _parse_api_key_map() -> dict[str, tuple[str, str]]:
    raw = os.getenv(
        "SOLAR_API_KEYS",
        "dev-admin-key:admin:dev-admin,dev-operator-key:operator:dev-operator,dev-analyst-key:analyst:dev-analyst,dev-viewer-key:viewer:dev-viewer,dev-ingest-key:ingestion:dev-ingest,dev-compliance-key:compliance:dev-compliance",
    )
    parsed: dict[str, tuple[str, str]] = {}
    for chunk in raw.split(","):
        piece = chunk.strip()
        if not piece:
            continue
        parts = piece.split(":")
        if len(parts) < 2:
            continue
        key = parts[0].strip()
        role = parts[1].strip()
        actor = parts[2].strip() if len(parts) >= 3 else role
        if key and role:
            parsed[key] = (role, actor)
    return parsed


def _extract_token(authorization: str | None, x_api_key: str | None) -> str | None:
    if x_api_key:
        return x_api_key.strip()
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return authorization.strip()


def get_principal(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Principal:
    token = _extract_token(authorization=authorization, x_api_key=x_api_key)
    require_key = os.getenv("SOLAR_REQUIRE_API_KEY", "true").lower() in {"1", "true", "yes"}

    if not token:
        if not require_key:
            return Principal(actor="anonymous", role="viewer", token_hint="anonymous")
        raise HTTPException(status_code=401, detail="Missing API key. Use header X-API-Key")

    mapping = _parse_api_key_map()
    if token not in mapping:
        raise HTTPException(status_code=403, detail="Invalid API key")

    role, actor = mapping[token]
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=403, detail=f"Unknown role mapped to API key: {role}")

    return Principal(actor=actor, role=role, token_hint=f"***{token[-4:]}" if len(token) >= 4 else "***")


def require_permission(permission: str) -> Callable[[Principal], Principal]:
    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.can(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required for role {principal.role}",
            )
        return principal

    return _dependency
