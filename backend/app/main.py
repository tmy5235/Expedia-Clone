from contextlib import asynccontextmanager
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Callable
from datetime import datetime

from fastapi import Cookie, FastAPI, HTTPException, Path as PathParameter, Query, Response
from fastapi.responses import JSONResponse
from app.config import load_geoapify_api_key
from app.schemas import StayResponse, TravelerResponse, BookingResponse, CreateBooking, CancelBooking, Credentials, HotelDiscoveryResponse
from app.controllers.accounts import AccountController
from app.controllers.search import SearchController
from app.controllers import discovery, locations

from app.database import Database, RecordNotFound


Session = Annotated[str | None, Cookie(alias="expedia_session")]


def create_app(database_path: Path | None = None, clock: Callable[[], datetime] | None = None) -> FastAPI:
    database = Database(database_path or Path(os.environ.get(
        "EXPEDIA_DB_PATH", Path(__file__).resolve().parents[1] / "data" / "expedia.sqlite3"
    )))

    accounts = AccountController(database)
    searches = SearchController(database, clock)
    geoapify_configured = False

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        nonlocal geoapify_configured
        geoapify_configured = bool(load_geoapify_api_key())
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

    @application.get("/api/health")
    def api_health() -> dict[str, str]:
        return {
            **health(),
            "geoapify": "key is configured" if geoapify_configured else "key is not configured",
        }

    def zip_location_response(postcode: str) -> locations.ZipLocation:
        try:
            location = locations.lookup_zip(postcode)
        except locations.GeoapifyConfigurationError:
            raise HTTPException(status_code=503, detail="Geoapify key is not configured.") from None
        except locations.GeoapifyRequestError:
            raise HTTPException(status_code=502, detail="Location provider request failed.") from None
        if location is None:
            raise HTTPException(status_code=404, detail=f"ZIP {postcode} could not be resolved.")
        return location

    @application.get("/api/demo/zip-location")
    def demo_zip_location() -> locations.ZipLocation:
        return zip_location_response("16802")

    @application.get("/api/zip-location")
    def get_zip_location(
        postcode: Annotated[str, Query(min_length=5, max_length=5, pattern=r"^[0-9]{5}$")],
    ) -> locations.ZipLocation:
        return zip_location_response(postcode)

    @application.post("/api/accounts", response_model=TravelerResponse, status_code=201)
    def create_account(credentials: Credentials) -> dict:
        return accounts.create(credentials.username, credentials.password)

    @application.get("/api/discovery/hotels", response_model=HotelDiscoveryResponse)
    def discover_hotels(
        postcode: Annotated[str, Query(min_length=5, max_length=5, pattern=r"^[0-9]{5}$")],
        response: Response,
    ) -> HotelDiscoveryResponse:
        response.headers["Cache-Control"] = "no-store"
        try:
            return discovery.discover_hotels(postcode)
        except discovery.UnresolvedZipError:
            raise HTTPException(status_code=404, detail=f"U.S. ZIP {postcode} could not be resolved.") from None
        except locations.GeoapifyConfigurationError:
            raise HTTPException(status_code=503, detail="Hotel search is not configured. Please contact the app owner.") from None
        except locations.GeoapifyRateLimitError:
            raise HTTPException(status_code=429, detail="The location provider's request limit was reached. Please try again later.") from None
        except locations.GeoapifyRequestError:
            raise HTTPException(status_code=502, detail="Hotel search failed because the location provider is unavailable or returned an invalid response. Please try again.") from None

    @application.post("/api/login", response_model=TravelerResponse)
    def login(credentials: Credentials, response: Response, session: Session = None) -> dict:
        user, token = accounts.login(credentials.username, credentials.password, session)
        response.set_cookie("expedia_session", token, httponly=True, samesite="strict", max_age=604800)
        return user

    @application.get("/api/session", response_model=TravelerResponse | None)
    def current_user(session: Session = None) -> dict | None:
        return accounts.current(session)

    @application.post("/api/logout", status_code=204)
    def logout(response: Response, session: Session = None) -> Response:
        database.delete_session(session)
        response.delete_cookie("expedia_session")
        response.status_code = 204
        return response

    @application.get("/api/stays", response_model=list[StayResponse])
    def get_stays(hotel_name: Annotated[str, Query(min_length=1, max_length=100)],
                  response: Response, session: Session = None) -> list[dict]:
        try:
            response.headers["Cache-Control"] = "no-store"
            return searches.submit(hotel_name, accounts.current(session))
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
        session: Session = None,
    ) -> list[dict]:
        accounts.require(session, user_id)
        return database.history(user_id)

    @application.post("/api/bookings", response_model=BookingResponse, status_code=201)
    def create_booking(booking: CreateBooking, session: Session = None) -> dict:
        accounts.require(session, booking.user_id)
        total = searches.booking_total(booking.user_id, booking.trip_id, booking.search_id)
        return database.create_booking(booking.user_id, booking.trip_id, total)

    @application.patch("/api/bookings/{booking_id}", response_model=BookingResponse)
    def cancel_booking(
        booking_id: Annotated[
            str, PathParameter(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
        booking: CancelBooking,
        session: Session = None,
    ) -> dict:
        accounts.require(session, booking.user_id)
        return database.cancel_booking(booking_id, booking.user_id)

    @application.delete("/api/bookings/{booking_id}", status_code=204)
    def delete_booking(
        booking_id: Annotated[
            str, PathParameter(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
        user_id: Annotated[
            str, Query(min_length=1, max_length=100, pattern=r"^\S+$")
        ],
        session: Session = None,
    ) -> Response:
        accounts.require(session, user_id)
        database.delete_booking(booking_id, user_id)
        return Response(status_code=204)

    return application


app = create_app()
