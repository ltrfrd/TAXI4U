# -----------------------------------------------------------
# - Load fares data
# - Reusable fare calculator for app integration
# -----------------------------------------------------------

import json
from zone_mapper import detect_zone, detect_possible_zones

with open("fares.json", "r") as f:                         # Load fare matrix
    fares = json.load(f)


# -----------------------------------------------------------
# - Calculate fare
# - Base fare + extra stops + waiting time
# -----------------------------------------------------------
def calculate_fare(pickup_zone, dropoff_zone, extra_stops=0, wait_minutes=0):
    try:
        base_fare = fares[pickup_zone][dropoff_zone]      # Matrix lookup
    except KeyError:
        return "Fare not found"

    stop_fee = extra_stops * 4                            # $4 per extra stop
    chargeable_wait = max(wait_minutes - 4, 0)            # First 4 min free
    wait_fee = chargeable_wait * 0.5                      # $0.50 per min after 4

    total = base_fare + stop_fee + wait_fee

    return {
        "pickup_zone": pickup_zone,
        "dropoff_zone": dropoff_zone,
        "base_fare": base_fare,
        "stop_fee": stop_fee,
        "wait_fee": wait_fee,
        "total": total,
    }


# -----------------------------------------------------------
# - Distance-based fallback pricing
# - $2 per km
# -----------------------------------------------------------
def calculate_distance_fare(distance_km: float) -> dict:
    fare = distance_km * 2
    return {
        "type": "distance_fare",
        "distance_km": distance_km,
        "rate_per_km": 2,
        "total_fare": round(fare, 2),
    }


# -----------------------------------------------------------
# - Prepare trip data
# - Build clean confirmation payload before fare calculation
# -----------------------------------------------------------
def prepare_trip_data(
    pickup_zone,
    dropoff_zone,
    extra_stops=0,
    wait_minutes=0,
    pickup_matches=None,
    dropoff_matches=None,
    distance_km=None,
):
    trip_data = {
        "pickup_zone": pickup_zone,
        "dropoff_zone": dropoff_zone,
        "pickup_matches": pickup_matches or [],
        "dropoff_matches": dropoff_matches or [],
        "extra_stops": extra_stops,
        "wait_minutes": wait_minutes,
        "ready_for_confirmation": True,
    }

    if distance_km is not None:
        trip_data["distance_km"] = distance_km

    return trip_data
# -----------------------------------------------------------
# - Validate trip data
# - Ensure required values exist before confirmation
# -----------------------------------------------------------
def validate_trip_data(trip_data):
    required_fields = ["pickup_zone", "dropoff_zone", "extra_stops", "wait_minutes"]

    for field in required_fields:
        if field not in trip_data:
            return {
                "valid": False,
                "message": f"Missing field: {field}",
            }

    if not trip_data["pickup_zone"]:
        return {
            "valid": False,
            "message": "Pickup zone is required",
        }

    if trip_data["pickup_zone"] == "Unknown Zone":
        return {
            "valid": False,
            "message": "Pickup zone is invalid",
        }

    if not trip_data["dropoff_zone"]:
        return {
            "valid": False,
            "message": "Drop-off zone is required",
        }

    if trip_data["dropoff_zone"] == "Unknown Zone":
        return {
            "valid": False,
            "message": "Drop-off zone is invalid",
        }

    if trip_data["extra_stops"] < 0:
        return {
            "valid": False,
            "message": "Extra stops cannot be negative",
        }

    if trip_data["wait_minutes"] < 0:
        return {
            "valid": False,
            "message": "Wait minutes cannot be negative",
        }

    return {
        "valid": True,
        "message": "Trip data is valid",
    }
# -----------------------------------------------------------
# - Confirm trip data
# - Pass confirmed trip details into fare calculation
# -----------------------------------------------------------
def confirm_and_calculate(trip_data):
    return calculate_fare(
        trip_data["pickup_zone"],
        trip_data["dropoff_zone"],
        extra_stops=trip_data["extra_stops"],
        wait_minutes=trip_data["wait_minutes"],
    )
