# -----------------------------------------------------------
# - TAXI4U API
# - First FastAPI entry point
# -----------------------------------------------------------

from fastapi import FastAPI
from calculator import (
    calculate_distance_fare,
    calculate_fare,
    prepare_trip_data,
    validate_trip_data,
)
from pydantic import BaseModel
# -----------------------------------------------------------
# Imports
# Fare request model + zone detection
# -----------------------------------------------------------
from pydantic import BaseModel
from zone_mapper import detect_zone, detect_possible_zones




app = FastAPI(title="TAXI4U Fare API")


# -----------------------------------------------------------
# - Root endpoint
# - Basic API health message
# -----------------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "TAXI4U Fare API is running"
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

# -----------------------------------------------------------
# Fare Request Model
# Accept pickup and dropoff text from user
# -----------------------------------------------------------


class FareRequest(BaseModel):
    pickup: str
    dropoff: str



# -----------------------------------------------------------
# Fare Request Model
# Accept pickup and dropoff text from user
# -----------------------------------------------------------
class FareRequest(BaseModel):
    pickup: str
    dropoff: str


# -----------------------------------------------------------
# POST /fare/calculate
# Step 3: Prepare + validate only
# -----------------------------------------------------------
@app.post("/fare/calculate")
def calculate_fare_endpoint(request: FareRequest):
    pickup_zone = detect_zone(request.pickup)
    dropoff_zone = detect_zone(request.dropoff)

    pickup_options = detect_possible_zones(request.pickup)
    dropoff_options = detect_possible_zones(request.dropoff)

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

    if validation_status == "valid" and validation["valid"]:
        return {
            "pickup_text": request.pickup,
            "dropoff_text": request.dropoff,
            "pickup_zone": pickup_zone,
            "dropoff_zone": dropoff_zone,
            "validation_status": "valid",
            "pickup_possible_zones": pickup_options,
            "dropoff_possible_zones": dropoff_options,
            "fare_type": "zone",
            "trip_data": trip_data,
            "validation": validation,
            "fare": calculate_fare(
                pickup_zone=trip_data["pickup_zone"],
                dropoff_zone=trip_data["dropoff_zone"],
                extra_stops=trip_data["extra_stops"],
                wait_minutes=trip_data["wait_minutes"],
            ),
        }

    return {
        "pickup_text": request.pickup,
        "dropoff_text": request.dropoff,
        "pickup_zone": pickup_zone,
        "dropoff_zone": dropoff_zone,
        "validation_status": validation_status,
        "pickup_possible_zones": pickup_options,
        "dropoff_possible_zones": dropoff_options,
        "pickup_options": pickup_options if pickup_ambiguous else [],
        "dropoff_options": dropoff_options if dropoff_ambiguous else [],
        "error": "Zone not recognized" if pickup_invalid or dropoff_invalid else None,
        "message": "Multiple possible zones detected" if pickup_ambiguous or dropoff_ambiguous else None,
        "fare_type": "distance",
        "trip_data": trip_data,
        "validation": validation,
        "fare": calculate_distance_fare(trip_data["distance_km"]),
    }
