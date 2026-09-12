import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "expedia-clone-data"


class HotelDataError(RuntimeError):
    """Raised when the supplied travel data cannot be read safely."""


def _read_csv(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fields = set(reader.fieldnames or [])
            missing_fields = required_fields - fields
            if missing_fields:
                missing = ", ".join(sorted(missing_fields))
                raise HotelDataError(f"{path.name} is missing required columns: {missing}.")
            return list(reader)
    except OSError as error:
        raise HotelDataError(f"Unable to read {path.name}.") from error
    except csv.Error as error:
        raise HotelDataError(f"Unable to parse {path.name}.") from error


def search_hotel_stays(
    hotel_name: str,
    data_directory: Path = DATA_DIRECTORY,
) -> list[dict[str, str | int]]:
    query = hotel_name.strip()
    if not query:
        raise ValueError("Enter a hotel name.")

    hotels = _read_csv(
        data_directory / "hotels.csv",
        {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"},
    )
    trips = _read_csv(
        data_directory / "trips.csv",
        {"trip_id", "hotel_id", "trip_name", "check_in", "check_out"},
    )

    matching_hotels = {
        hotel["hotel_id"]: hotel
        for hotel in hotels
        if query.casefold() in hotel["hotel_name"].casefold()
    }

    stays: list[dict[str, str | int]] = []
    for trip in trips:
        hotel = matching_hotels.get(trip["hotel_id"])
        if hotel is None:
            continue

        try:
            check_in = date.fromisoformat(trip["check_in"])
            check_out = date.fromisoformat(trip["check_out"])
            nightly_rate_cents = int(Decimal(hotel["nightly_rate_usd"]) * 100)
        except (ValueError, InvalidOperation) as error:
            raise HotelDataError("The supplied travel data contains an invalid date or rate.") from error

        nights = (check_out - check_in).days
        if nights <= 0:
            raise HotelDataError("The supplied travel data contains an invalid stay date range.")

        stays.append(
            {
                "trip_id": trip["trip_id"],
                "trip_name": trip["trip_name"],
                "hotel_id": hotel["hotel_id"],
                "hotel_name": hotel["hotel_name"],
                "city": hotel["city"],
                "state": hotel["state"],
                "check_in": trip["check_in"],
                "check_out": trip["check_out"],
                "nights": nights,
                "nightly_rate_cents": nightly_rate_cents,
                "total_cents": nightly_rate_cents * nights,
            }
        )

    return sorted(stays, key=lambda stay: (str(stay["hotel_name"]), str(stay["trip_id"])))
