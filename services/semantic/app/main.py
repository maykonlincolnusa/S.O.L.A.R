from fastapi import FastAPI

from shared.solar_common import init_db
from services.semantic.app.routes import router

app = FastAPI(title="SOLAR Semantic Service", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "semantic"}


app.include_router(router)

