from __future__ import annotations

import json
from pathlib import Path


def _load_zones():
    zones_path = Path(__file__).resolve().parent / "backend" / "data" / "zones.json"
    with zones_path.open("r", encoding="utf-8") as zones_file:
        return json.load(zones_file)


def _build_bounds(polygon):
    latitudes = [point["latitude"] for point in polygon]
    longitudes = [point["longitude"] for point in polygon]
    return {
        "lat_min": min(latitudes),
        "lat_max": max(latitudes),
        "lon_min": min(longitudes),
        "lon_max": max(longitudes),
    }


ZONES = _load_zones()
ZONE_BOUNDARIES = {
    zone["name"]: _build_bounds(zone["polygon"])
    for zone in ZONES
}


# Shrinks bounding box checks inward to reduce edge/overlap mismatches.
BUFFER = 0.0008

# Evaluation order for detect_zone_by_coords.
# Smaller and more specific zones are listed first so they win when boxes overlap.
ZONE_PRIORITY = [zone["name"] for zone in sorted(ZONES, key=lambda zone: zone["priority"])]


ZONE_PATTERNS = {
    "Downtown/Quarry": [
        "downtown",
        "quarry",
    ],
    "East End/Industrial": [
        "east end",
        "industrial",
    ],
    "Riverview/Greystone": [
        "riverview",
        "greystone",
    ],
    "SLS Centre (SLRC)": [
        "sls",
        "slrc",
        "sls centre",
    ],
    "Glenbow": [
        "glenbow",
    ],
    "West Valley/Mitford": [
        "west valley",
        "mitford",
    ],
    "West Terrace/Pointe": [
        "west terrace",
        "terrace",
        "pointe",
    ],
    "Cochrane Heights": [
        "cochrane heights",
        "heights",
    ],
    "Sunterra": [
        "sunterra",
    ],
    "Fireside (Residential)": [
        "fireside",
        "fireside residential",
    ],
    "Riversong/BVHS": [
        "riversong",
        "bvhs",
    ],
    "Riviera/Precedence": [
        "riviera",
        "precedence",
    ],
    "Sunset (Before Sunset Rd)": [
        "sunset",
        "before sunset",
    ],
    "Airports (All)": [
        "airport",
        "airports",
        "yyc",
        "yeg",
        "edmonton airport",
        "calgary airport",
    ],
}


def normalize_text(text_input):
    return text_input.lower().strip()


def detect_possible_zones(text_input):
    text = normalize_text(text_input)
    matches = []

    for zone_name, keywords in ZONE_PATTERNS.items():
        for keyword in keywords:
            if keyword in text:
                matches.append(zone_name)
                break

    return matches


def detect_zone(text_input):
    matches = detect_possible_zones(text_input)

    if matches:
        return matches[0]

    return "Unknown Zone"


def detect_zone_by_coords(lat: float, lon: float) -> str | None:
    for zone_name in ZONE_PRIORITY:
        bounds = ZONE_BOUNDARIES[zone_name]
        if (
            bounds["lat_min"] + BUFFER <= lat <= bounds["lat_max"] - BUFFER
            and bounds["lon_min"] + BUFFER <= lon <= bounds["lon_max"] - BUFFER
        ):
            return zone_name
    return None
