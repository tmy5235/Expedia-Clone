from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.hotel_search import HotelDataError, search_hotel_stays


app = FastAPI(title="Expedia Clone API")


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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stays", response_model=list[StayResponse])
async def get_stays(
    hotel_name: Annotated[str, Query(min_length=1, max_length=100)],
) -> list[dict[str, str | int]]:
    try:
        return search_hotel_stays(hotel_name)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except HotelDataError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
