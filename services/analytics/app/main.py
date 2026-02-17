from fastapi import FastAPI

from shared.solar_common import init_db
from services.analytics.app.routes import router

app = FastAPI(title="SOLAR Analytics Service", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analytics"}


app.include_router(router)

