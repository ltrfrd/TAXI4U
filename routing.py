# -----------------------------------------------------------
# - Routing
# - Gets driving distance and duration between two GPS points via OSRM
# -----------------------------------------------------------

import requests

from config import OSRM_URL


def get_route(origin: dict, destination: dict) -> dict | None:
    coords = f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
    url = f"{OSRM_URL}/{coords}"
    params = {"overview": "false", "steps": "false"}
    try:
        response = requests.get(url, params=params, timeout=6)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            return {
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_minutes": round(route["duration"] / 60, 1),
            }
    except Exception:
        pass
    return None
