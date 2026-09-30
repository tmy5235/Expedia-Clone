"""Live hotel discovery, independent of fictional stays and booking prices."""

import math

from app.controllers import locations
from app.schemas import DiscoveredHotel, HotelDiscoveryResponse

RADIUS_METERS = 5000
RESULT_LIMIT = 20


class UnresolvedZipError(ValueError):
    """The requested U.S. postcode could not be established."""


def optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def distance_meters(lat: float, lon: float, center: locations.ZipLocation) -> float:
    """Great-circle distance, used only to enforce the requested search radius."""
    phi, center_phi = math.radians(lat), math.radians(center["latitude"])
    delta_phi = phi - center_phi
    delta_lambda = math.radians(lon - center["longitude"])
    haversine = (math.sin(delta_phi / 2) ** 2
                 + math.cos(phi) * math.cos(center_phi) * math.sin(delta_lambda / 2) ** 2)
    return 6371008.8 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, haversine))))


def discover_hotels(postcode: str) -> HotelDiscoveryResponse:
    center = locations.lookup_zip(postcode)
    if center is None:
        raise UnresolvedZipError("U.S. ZIP could not be resolved.")
    lon, lat = center["longitude"], center["latitude"]
    payload = locations.request_geoapify("/v2/places", {
        "categories": "accommodation.hotel",
        "filter": f"circle:{lon},{lat},{RADIUS_METERS}",
        "bias": f"proximity:{lon},{lat}",
        "limit": RESULT_LIMIT,
    })
    if (not isinstance(payload, dict) or payload.get("type") != "FeatureCollection"
            or not isinstance(payload.get("features"), list)):
        raise locations.GeoapifyRequestError("Geoapify returned an invalid response.")
    features = payload["features"]
    hotels: list[DiscoveredHotel] = []
    seen: set[str] = set()
    for feature in features[:RESULT_LIMIT]:
        if not isinstance(feature, dict):
            continue
        props, geometry = feature.get("properties"), feature.get("geometry")
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            continue
        place_id = optional_text(props.get("place_id"))
        coordinates = geometry.get("coordinates")
        if (not place_id or place_id in seen or geometry.get("type") != "Point"
                or not isinstance(coordinates, list) or len(coordinates) < 2):
            continue
        longitude, latitude = coordinates[:2]
        if not all(type(value) in (int, float) and math.isfinite(value)
                   for value in (longitude, latitude)):
            continue
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            continue
        if distance_meters(latitude, longitude, center) > RADIUS_METERS:
            continue
        hotels.append(DiscoveredHotel(
            place_id=place_id, name=optional_text(props.get("name")),
            address=optional_text(props.get("formatted")),
            latitude=latitude, longitude=longitude,
        ))
        seen.add(place_id)
    return HotelDiscoveryResponse(
        center=center, radius_meters=RADIUS_METERS, result_limit=RESULT_LIMIT,
        limit_reached=len(features) >= RESULT_LIMIT,
        omitted_count=len(features) - len(hotels), hotels=hotels,
    )
