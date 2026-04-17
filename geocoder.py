# -----------------------------------------------------------
# - Geocoder
# - Converts address strings into GPS coordinates via Nominatim
# -----------------------------------------------------------

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "TAXI4U-FareCalculator/1.0"}

_cache: dict[str, dict | None] = {}


def geocode_address(address: str) -> dict | None:
    cache_key = address.strip().lower()

    if cache_key in _cache:
        return _cache[cache_key]

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }
    result = None
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=6)
        response.raise_for_status()
        results = response.json()
        if results:
            r = results[0]
            result = {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "display_name": r["display_name"],
            }
    except Exception:
        pass

    _cache[cache_key] = result
    return result
