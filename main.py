# -----------------------------------------------------------
# - TAXI4U API
# - FastAPI entry point with address geocoding + routing support
# -----------------------------------------------------------

from fastapi import FastAPI
from pydantic import BaseModel

import database
import models.driver          # registers Driver table with Base metadata
import models.driver_location  # registers DriverLocation table with Base metadata
from routers.driver import router as driver_router
from calculator import (
    calculate_distance_fare,
    calculate_fare,
    prepare_trip_data,
    validate_trip_data,
)
from geocoder import geocode_address, normalize_input
from routing import get_route
from zone_mapper import ZONES, detect_zone, detect_possible_zones, detect_zone_by_coords


app = FastAPI(title="TAXI4U Fare API")

database.Base.metadata.create_all(bind=database.engine)
app.include_router(driver_router)

DISTANCE_FALLBACK_KM = 10


# -----------------------------------------------------------
# - Root endpoint
# - Basic API health message
# -----------------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "TAXI4U Fare API is running"
    }


@app.get("/zones")
def get_zones():
    return {
        "zones": ZONES
    }


# -----------------------------------------------------------
# - Fare test endpoint
# - Simple fixed test using current fare engine
# -----------------------------------------------------------
@app.get("/fare/test")
def fare_test():
    trip = prepare_trip_data(
        pickup_zone="Downtown/Quarry",
        dropoff_zone="Glenbow",
        extra_stops=1,
        wait_minutes=6,
    )

    validation = validate_trip_data(trip)

    if not validation["valid"]:
        return {
            "ok": False,
            "error": validation["message"],
        }

    result = calculate_fare(
        pickup_zone=trip["pickup_zone"],
        dropoff_zone=trip["dropoff_zone"],
        extra_stops=trip["extra_stops"],
        wait_minutes=trip["wait_minutes"],
    )

    return {
        "ok": True,
        "trip": trip,
        "fare": result,
    }


class FareLocationCoords(BaseModel):
    lat: float
    lon: float
    display_name: str | None = None


# -----------------------------------------------------------
# - Fare Request Model
# - Accept pickup and dropoff address strings
# -----------------------------------------------------------
class FareRequest(BaseModel):
    pickup: str
    dropoff: str
    pickup_coords: FareLocationCoords | None = None
    dropoff_coords: FareLocationCoords | None = None


# -----------------------------------------------------------
# POST /fare/calculate
# Geocodes addresses, routes, detects zones, applies fare logic
# -----------------------------------------------------------
@app.post("/fare/calculate")
def calculate_fare_endpoint(request: FareRequest):
    # --- Validate inputs before any geocoding ---
    _, pickup_err = normalize_input(request.pickup)
    _, dropoff_err = normalize_input(request.dropoff)
    if pickup_err or dropoff_err:
        return {
            "ok": False,
            "error": pickup_err or dropoff_err,
            "pickup_error": pickup_err,
            "dropoff_error": dropoff_err,
            "distance": None,
            "confidence": "low",
            "method_used": None,
        }

    # --- Use provided coords when present; otherwise geocode as before ---
    pickup_coords = provided_or_geocoded_coords(request.pickup_coords, request.pickup)
    if pickup_coords is None:
        pickup_coords = safe_geocode_address(request.pickup)

    dropoff_coords = provided_or_geocoded_coords(request.dropoff_coords, request.dropoff)
    if dropoff_coords is None:
        dropoff_coords = safe_geocode_address(request.dropoff)

    # --- Get real route distance/duration (always, for driver convenience) ---
    route = None
    if pickup_coords and dropoff_coords:
        route = safe_get_route(pickup_coords, dropoff_coords)

    # --- Zone detection: coords → geocoded display_name → raw text ---
    def resolve_zone(coords, raw_text):
        detection_text = coords["display_name"] if coords else raw_text
        if coords:
            coord_zone = detect_zone_by_coords(coords["lat"], coords["lon"])
            if coord_zone:
                return coord_zone, [coord_zone], "coords", detection_text
            source = "geocoded"
        else:
            source = "raw"
        return detect_zone(detection_text), detect_possible_zones(detection_text), source, detection_text

    pickup_zone, pickup_options, pickup_detection_source, pickup_detection_text = resolve_zone(pickup_coords, request.pickup)
    dropoff_zone, dropoff_options, dropoff_detection_source, dropoff_detection_text = resolve_zone(dropoff_coords, request.dropoff)

    pickup_invalid = pickup_zone in (None, "Unknown Zone") or len(pickup_options) == 0
    dropoff_invalid = dropoff_zone in (None, "Unknown Zone") or len(dropoff_options) == 0
    pickup_ambiguous = len(pickup_options) > 1
    dropoff_ambiguous = len(dropoff_options) > 1

    if pickup_invalid or dropoff_invalid:
        validation_status = "invalid"
    elif pickup_ambiguous or dropoff_ambiguous:
        validation_status = "ambiguous"
    else:
        validation_status = "valid"

    trip_data = prepare_trip_data(
        pickup_zone=pickup_zone,
        dropoff_zone=dropoff_zone,
        pickup_matches=pickup_options,
        dropoff_matches=dropoff_options,
    )

    validation = validate_trip_data(trip_data)

    _confidence = {"coords": "high", "geocoded": "medium", "raw": "low"}
    overall_confidence = get_overall_confidence(
        pickup_detection_source,
        dropoff_detection_source,
    )
    distance = route["distance_km"] if route else DISTANCE_FALLBACK_KM

    # --- Base response fields shared by both fare types ---
    base = {
        "pickup_text": request.pickup,
        "dropoff_text": request.dropoff,
        "pickup_zone": pickup_zone,
        "dropoff_zone": dropoff_zone,
        "validation_status": validation_status,
        "pickup_possible_zones": pickup_options,
        "dropoff_possible_zones": dropoff_options,
        "pickup_coords": pickup_coords,
        "dropoff_coords": dropoff_coords,
        "pickup_detection_source": pickup_detection_source,
        "dropoff_detection_source": dropoff_detection_source,
        "pickup_detection_text": pickup_detection_text,
        "dropoff_detection_text": dropoff_detection_text,
        "pickup_detection_confidence": _confidence[pickup_detection_source],
        "dropoff_detection_confidence": _confidence[dropoff_detection_source],
        "route": route,
        "distance": distance,
        "confidence": overall_confidence,
        "trip_data": trip_data,
        "validation": validation,
    }

    # --- Business rule: zone fare if both zones resolve in chart ---
    zone_fare = calculate_fare(
        pickup_zone=trip_data["pickup_zone"],
        dropoff_zone=trip_data["dropoff_zone"],
        extra_stops=trip_data["extra_stops"],
        wait_minutes=trip_data["wait_minutes"],
    )

    if validation_status == "valid" and validation["valid"] and isinstance(zone_fare, dict):
        return {
            **base,
            "fare_type": "zone",
            "method_used": "zone",
            "fare": zone_fare,
        }

    # --- Distance fallback: use real route distance, or hardcoded fallback ---
    distance_km = distance

    fallback_trip_data = {**trip_data, "distance_km": distance_km}

    return {
        **base,
        "trip_data": fallback_trip_data,
        "pickup_options": pickup_options if pickup_ambiguous else [],
        "dropoff_options": dropoff_options if dropoff_ambiguous else [],
        "error": "Zone not recognized" if pickup_invalid or dropoff_invalid else None,
        "message": "Multiple possible zones detected" if pickup_ambiguous or dropoff_ambiguous else None,
        "fare_type": "distance",
        "method_used": "distance",
        "fare": calculate_distance_fare(distance_km),
    }


def provided_or_geocoded_coords(coords: FareLocationCoords | None, fallback_text: str) -> dict | None:
    if coords is None:
        return None

    return {
        "lat": coords.lat,
        "lon": coords.lon,
        "display_name": coords.display_name or fallback_text,
    }


def safe_geocode_address(address: str) -> dict | None:
    try:
        return geocode_address(address)
    except Exception:
        return None


def safe_get_route(origin: dict, destination: dict) -> dict | None:
    try:
        return get_route(origin, destination)
    except Exception:
        return None


def get_overall_confidence(pickup_source: str, dropoff_source: str) -> str:
    if pickup_source == "coords" and dropoff_source == "coords":
        return "high"
    if "raw" not in {pickup_source, dropoff_source} and (
        "geocoded" in {pickup_source, dropoff_source}
    ):
        return "medium"
    return "low"
