"""Local persistence contracts, separate from the frozen Part 1 response models."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProviderId = Annotated[str, Field(strict=True, min_length=1, max_length=2048)]
Postcode = Annotated[str, Field(strict=True, pattern=r'^[0-9]{5}$')]
Latitude = Annotated[float, Field(strict=True, ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(strict=True, ge=-180, le=180, allow_inf_nan=False)]


class LocalPlace(BaseModel):
    model_config = ConfigDict(extra='forbid')
    place_id: ProviderId
    name: str | None = Field(default=None, max_length=2000)
    address: str | None = Field(default=None, max_length=4000)
    latitude: Latitude
    longitude: Longitude

    @field_validator('place_id')
    @classmethod
    def nonempty_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Provider hotel ID must not be blank.')
        return value  # Provider IDs are opaque: never trim or casefold them.


class LocalCenter(BaseModel):
    model_config = ConfigDict(extra='forbid')
    postcode: Postcode
    country_code: Literal['us']
    locality: str | None = Field(default=None, max_length=2000)
    latitude: Latitude
    longitude: Longitude


class SaveLocalHotel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hotel: LocalPlace
    center: LocalCenter


class DemoNight(BaseModel):
    stay_date: date
    nightly_rate_cents: int = Field(ge=0)
    rooms_available: int = Field(ge=0)


class SavedHotel(LocalPlace):
    demo_nights: list[DemoNight]


class LocalSearchResponse(BaseModel):
    provider: Literal['geoapify'] = 'geoapify'
    source: Literal['local'] = 'local'
    center: LocalCenter | None
    radius_meters: Literal[5000] = 5000
    hotels: list[SavedHotel]


class HotelStatusRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    place_ids: list[ProviderId] = Field(max_length=20)


class HotelStatusResponse(BaseModel):
    saved_ids: list[str]
