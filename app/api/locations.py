from fastapi import APIRouter, HTTPException, Query

from app.schemas.location import LocationSearchResult
from app.services.location import LocationProviderError, search_locations

router = APIRouter(
    prefix="/api/locations",
    tags=["locations"],
)


@router.get(
    "/search",
    response_model=list[LocationSearchResult],
)
def search_location(
    q: str = Query(..., min_length=2, max_length=100),
):
    try:
        return search_locations(q)

    except LocationProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail="Location provider unavailable",
        ) from exc
