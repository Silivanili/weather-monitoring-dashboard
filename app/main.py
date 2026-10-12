from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.locations import router as locations_router
from app.api.weather import router as weather_router
from app.db.database import Base, check_database_connection, engine
from app.web.routes import router as index_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Weather Monitoring Dashboard",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/health")
def get_health():
    return {"status": "ok"}


@app.get("/ready")
def get_ready():
    if not check_database_connection():
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return {"status": "ready"}


app.include_router(weather_router)
app.include_router(locations_router)
app.include_router(index_router)
