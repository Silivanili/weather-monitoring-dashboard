from fastapi import FastAPI

from app.api.locations import router as locations_router
from app.api.weather import router as weather_router
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Weather Monitoring Dashboard",
    version="0.1.0",
)


@app.get("/health")
def get_health():
    return {"status": "ok"}


app.include_router(weather_router)
app.include_router(locations_router)
