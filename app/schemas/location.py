from pydantic import BaseModel


class LocationSearchResult(BaseModel):
    name: str
    country: str
    latitude: float
    longitude: float
