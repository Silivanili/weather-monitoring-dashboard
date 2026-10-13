from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.location import LocationProviderError, search_locations

DEFAULT_LATITUDE = 46.84986
DEFAULT_LONGITUDE = 9.53287

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    locations = []
    error = None
    if latitude is None and longitude is None:
        latitude = DEFAULT_LATITUDE
        longitude = DEFAULT_LONGITUDE
    if q is not None and len(q.strip()) >= 2:
        try:
            locations = search_locations(q.strip())

        except LocationProviderError:
            error = "Standortsuche momentan nicht verfügbar."
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "locations": locations,
            "q": q,
            "error": error,
            "latitude": latitude,
            "longitude": longitude,
        },
    )
