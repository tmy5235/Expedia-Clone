"""Validated HTTP input and public response shapes."""
import re
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StayResponse(BaseModel):
    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: str
    check_out: str
    nights: int
    nightly_rate_cents: int
    total_cents: int
    search_id: int | None = None
    search_count: int = 0


class TravelerResponse(BaseModel):
    user_id: str
    display_name: str
    username: str


class BookingResponse(BaseModel):
    booking_id: str
    user_id: str
    trip_id: str
    booked_on: str
    status: Literal['confirmed', 'cancelled']
    display_name: str
    trip_name: str
    hotel_name: str
    check_in: str
    check_out: str
    total_cents: int


Identifier = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^\S+$")]


class CreateBooking(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Identifier
    trip_id: Identifier
    search_id: int = Field(gt=0)


class CancelBooking(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Identifier
    status: Literal['cancelled']


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=100)

    @field_validator('username')
    @classmethod
    def valid_username(cls, value: str) -> str:
        value = value.strip().casefold()
        if not re.fullmatch(r'[a-z0-9_]{3,40}', value):
            raise ValueError('Use 3–40 letters, numbers, or underscores for your username.')
        return value

    @field_validator('password')
    @classmethod
    def valid_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Enter a password.')
        return value


class DiscoveryCenter(BaseModel):
    postcode: str
    country_code: Literal['us']
    latitude: float
    longitude: float
    locality: str | None = None


class DiscoveredHotel(BaseModel):
    """An external place is not a priced sample stay or a reservation."""
    place_id: str
    name: str | None = None
    address: str | None = None
    latitude: float
    longitude: float


class HotelDiscoveryResponse(BaseModel):
    provider: Literal['geoapify'] = 'geoapify'
    center: DiscoveryCenter
    radius_meters: int
    result_limit: int
    limit_reached: bool
    omitted_count: int
    hotels: list[DiscoveredHotel]
