from contextlib import asynccontextmanager
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path as PathParameter, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.database import Database, RecordNotFound


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


class TravelerResponse(BaseModel):
    user_id: str
    display_name: str


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


class CancelBooking(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Identifier
    status: Literal['cancelled']


def create_app(database_path: Path | None = None) -> FastAPI:
    database = Database(database_path or Path(os.environ.get(
        "EXPEDIA_DB_PATH", Path(__file__).resolve().parents[1] / "data" / "expedia.sqlite3"
    )))

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        database.initialize()
        yield

    application = FastAPI(title="Expedia Clone API", lifespan=lifespan)

    @application.exception_handler(RecordNotFound)
    async def not_found(_request, error: RecordNotFound):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @application.exception_handler(sqlite3.Error)
    async def storage_error(_request, _error: sqlite3.Error):
        return JSONResponse(status_code=503, content={"detail": "Database unavailable. Please try again."})

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/stays", response_model=list[StayResponse])
    def get_stays(hotel_name: Annotated[str, Query(min_length=1, max_length=100)]) -> list[dict]:
        try:
            return database.search(hotel_name)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @application.get("/api/users", response_model=list[TravelerResponse])
    def get_users() -> list[dict]:
        return database.users()

    @application.get("/api/bookings", response_model=list[BookingResponse])
    def get_bookings(
        user_id: Annotated[
            str, Query(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
    ) -> list[dict]:
        return database.history(user_id)

    @application.post("/api/bookings", response_model=BookingResponse, status_code=201)
    def create_booking(booking: CreateBooking) -> dict:
        return database.create_booking(booking.user_id, booking.trip_id)

    @application.patch("/api/bookings/{booking_id}", response_model=BookingResponse)
    def cancel_booking(
        booking_id: Annotated[
            str, PathParameter(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
        booking: CancelBooking,
    ) -> dict:
        return database.cancel_booking(booking_id, booking.user_id)

    @application.delete("/api/bookings/{booking_id}", status_code=204)
    def delete_booking(
        booking_id: Annotated[
            str, PathParameter(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
        user_id: Annotated[
            str, Query(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
    ) -> Response:
        database.delete_booking(booking_id, user_id)
        return Response(status_code=204)

    return application


app = create_app()
