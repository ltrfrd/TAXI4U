# -----------------------------------------------------------
# - Geocoder
# - Converts address strings into GPS coordinates via Nominatim
# - Anchors queries to Cochrane, AB when no geographic context
#   is present in the input, and rejects results outside the
#   service area before they can produce absurd routes/fares.
# -----------------------------------------------------------

import math
import re

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "TAXI4U-FareCalculator/1.0"}

_cache: dict[str, dict | None] = {}

# Cochrane, AB town centre
_COCHRANE_LAT = 51.1889
_COCHRANE_LON = -114.4664

# 300 km covers YEG airport (~240 km) + comfortable buffer;
# blocks anything clearly outside the service province.
_MAX_SERVICE_KM = 300

# Words that signal the query already carries geographic context.
# When present we skip the Cochrane anchor and trust the user's phrasing.
_GEO_ANCHORS = {
    "cochrane", "alberta", "canada",
    "calgary", "edmonton", "banff", "canmore",
    "yyc", "yeg", "ab",
}


# -----------------------------------------------------------
# Public helper — also used by main.py for early validation
# -----------------------------------------------------------
def normalize_input(text: str) -> tuple[str, str | None]:
    """
    Validate and lightly normalize a user-supplied location string.

    Returns (cleaned_text, error_message).
    error_message is None when the input is usable.
    """
    if not isinstance(text, str) or not text.strip():
        return "", "Please enter a location."

    # Collapse repeated whitespace and trim edges
    cleaned = re.sub(r"\s+", " ", text.strip())

    # Must contain at least one letter or digit
    if not re.search(r"[a-zA-Z0-9]", cleaned):
        return cleaned, "Location must include letters or numbers."

    # Single character is not specific enough
    if len(cleaned.replace(" ", "")) < 2:
        return cleaned, "Location is too short — please be more specific."

    return cleaned, None


# -----------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------
def _has_geo_anchor(text: str) -> bool:
    """True if the text already names a recognisable geographic anchor."""
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    return bool(tokens & _GEO_ANCHORS)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _within_service_area(lat: float, lon: float) -> bool:
    return _haversine_km(_COCHRANE_LAT, _COCHRANE_LON, lat, lon) <= _MAX_SERVICE_KM


def _fetch(query: str) -> dict | None:
    """Send one query to Nominatim with per-query caching."""
    key = query.strip().lower()
    if key in _cache:
        return _cache[key]

    params = {"q": query, "format": "json", "limit": 1}
    result = None
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=6)
        response.raise_for_status()
        hits = response.json()
        if hits:
            r = hits[0]
            result = {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "display_name": r["display_name"],
            }
    except Exception:
        pass

    _cache[key] = result
    return result


# -----------------------------------------------------------
# Public geocoding entry point
# -----------------------------------------------------------
def geocode_address(address: str) -> dict | None:
    """
    Geocode an address string.

    Strategy:
      1. Normalize and validate input — return None for garbage.
      2. If the query already mentions Cochrane / Alberta / known
         anchor words, use it as-is.
      3. Otherwise try:
           a) "{input}, Cochrane, Alberta, Canada"   (most specific)
           b) "{input}, Alberta, Canada"              (fallback for
                                                       airports etc.)
      4. Accept only results within _MAX_SERVICE_KM of Cochrane.
         A result that geocodes outside the service area is treated
         as a failed lookup so it cannot feed an absurd route fare.
    """
    normalized, error = normalize_input(address)
    if error:
        return None

    if _has_geo_anchor(normalized):
        queries = [normalized]
    else:
        queries = [
            f"{normalized}, Cochrane, Alberta, Canada",
            f"{normalized}, Alberta, Canada",
        ]

    for query in queries:
        result = _fetch(query)
        if result is None:
            continue  # nothing found — try next variant
        if _within_service_area(result["lat"], result["lon"]):
            return result
        # Found a place but it is outside the service area.
        # A more generic query won't fix this — stop.
        break

    return None
