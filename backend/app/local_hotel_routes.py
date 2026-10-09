"""Additive endpoints; the Part 1 discovery endpoint remains unchanged."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

from app.controllers.local_hotels import LocalHotelController
from app.database import Database
from app.local_hotel_schemas import (
    HotelStatusRequest, HotelStatusResponse, LocalSearchResponse, SaveLocalHotel, SavedHotel,
)
from app.saved_hotels import SavedHotelStore


def local_hotel_router(database: Database) -> APIRouter:
    router = APIRouter(prefix='/api/local-hotels')
    controller = LocalHotelController(SavedHotelStore(database))

    @router.get('', response_model=LocalSearchResponse)
    def search(postcode: Annotated[str, Query(pattern=r'^[0-9]{5}$')], response: Response) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        return controller.search(postcode)

    @router.post('', response_model=SavedHotel)
    def save(request: SaveLocalHotel, response: Response) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        try:
            return controller.save(request)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @router.post('/status', response_model=HotelStatusResponse)
    def status(request: HotelStatusRequest, response: Response) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        return {'saved_ids': controller.saved_ids(request.place_ids)}

    @router.delete('', status_code=204)
    def remove(hotel_id: Annotated[str, Query(min_length=1, max_length=2048)]) -> Response:
        if not hotel_id.strip():
            raise HTTPException(status_code=422, detail='Provider hotel ID must not be blank.')
        controller.remove(hotel_id)
        return Response(status_code=204, headers={'Cache-Control': 'no-store'})

    return router
