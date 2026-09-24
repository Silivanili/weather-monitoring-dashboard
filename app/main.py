from fastapi import FastAPI

from app.api.weather import router as weather_router

app = FastAPI(
    title="Weather Monitoring Dashboard",
    version="0.1.0",
)

app.include_router(weather_router)
