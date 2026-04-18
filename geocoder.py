# -----------------------------------------------------------
# - Geocoder
# - Converts address strings into GPS coordinates via Nominatim
# - Anchors queries to Cochrane, AB for weak/local inputs.
# - All Nominatim requests are restricted to Canada (countrycodes=ca)
#   so results outside the country are rejected at the API level.
# -----------------------------------------------------------

import re

import requests

from config import NOMINATIM_HEADERS, NOMINATIM_URL

HEADERS = NOMINATIM_HEADERS

_cache: dict[str, dict | None] = {}

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


def _fetch(query: str) -> dict | None:
    """Send one query to Nominatim (Canada-only) with per-query caching."""
    key = query.strip().lower()
    if key in _cache:
        return _cache[key]

    params = {"q": query, "format": "json", "limit": 1, "countrycodes": "ca"}
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
    Geocode an address string, restricted to Canada.

    Strategy:
      1. Normalize and validate — return None for garbage input.
      2. If the query already contains a geographic anchor word
         (cochrane, alberta, calgary, yyc, …) use it as-is.
      3. Otherwise try three progressively broader queries, all
         restricted to Canada via countrycodes=ca:
           a) "{input}, Cochrane, Alberta, Canada"  — best for local
              street-level or neighbourhood inputs
           b) "{input}, Alberta, Canada"            — catches airports,
              POIs that aren't in Cochrane proper
           c) "{input}"  (bare, still Canada-only)  — resolves any
              valid Canadian city or place name
      Returns the first query that produces a result, or None if all fail.
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
            normalized,
        ]

    for query in queries:
        result = _fetch(query)
        if result is not None:
            return result

    return None
