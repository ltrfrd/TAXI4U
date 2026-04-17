# -----------------------------------------------------------
# - Zone Mapper (Improved Version)
# - Converts raw text/location input into a mapped zone
# - Supports coordinate-based detection via bounding boxes
# -----------------------------------------------------------

# -----------------------------------------------------------
# Bounding boxes for coordinate-based zone detection.
# Each entry: lat_min, lat_max, lon_min, lon_max
# Covers a starting set of zones; expand as needed.
# Coordinates are approximate — text detection remains the fallback.
# -----------------------------------------------------------
ZONE_BOUNDARIES = {
    "Downtown/Quarry": {
        "lat_min": 51.183, "lat_max": 51.200,
        "lon_min": -114.478, "lon_max": -114.450,
    },
    "Glenbow": {
        "lat_min": 51.178, "lat_max": 51.195,
        "lon_min": -114.455, "lon_max": -114.428,
    },
    "Fireside (Residential)": {
        "lat_min": 51.160, "lat_max": 51.182,
        "lon_min": -114.505, "lon_max": -114.462,
    },
    "Bow Ridge/Jumping Pound": {
        "lat_min": 51.190, "lat_max": 51.220,
        "lon_min": -114.510, "lon_max": -114.470,
    },
    "East End/Industrial": {
        "lat_min": 51.178, "lat_max": 51.198,
        "lon_min": -114.430, "lon_max": -114.400,
    },
    "Riverview/Greystone": {
        "lat_min": 51.172, "lat_max": 51.187,
        "lon_min": -114.470, "lon_max": -114.443,
    },
    "West Valley/Mitford": {
        "lat_min": 51.193, "lat_max": 51.210,
        "lon_min": -114.498, "lon_max": -114.472,
    },
    "Riversong/BVHS": {
        "lat_min": 51.183, "lat_max": 51.195,
        "lon_min": -114.508, "lon_max": -114.483,
    },
    "West Terrace/Pointe": {
        "lat_min": 51.185, "lat_max": 51.198,
        "lon_min": -114.492, "lon_max": -114.472,
    },
    "Cochrane Heights": {
        "lat_min": 51.198, "lat_max": 51.215,
        "lon_min": -114.475, "lon_max": -114.448,
    },
    "Sunterra": {
        "lat_min": 51.175, "lat_max": 51.189,
        "lon_min": -114.495, "lon_max": -114.470,
    },
    "Willows/Rivercrest/Ford": {
        "lat_min": 51.168, "lat_max": 51.182,
        "lon_min": -114.490, "lon_max": -114.460,
    },
    "Riviera/Precedence": {
        "lat_min": 51.168, "lat_max": 51.183,
        "lon_min": -114.458, "lon_max": -114.428,
    },
    "Bow Meadows/Crawford": {
        "lat_min": 51.170, "lat_max": 51.186,
        "lon_min": -114.420, "lon_max": -114.393,
    },
    "H.Land/Heritage (Shallow)": {
        "lat_min": 51.205, "lat_max": 51.222,
        "lon_min": -114.462, "lon_max": -114.435,
    },
    "H.Land/Heritage (Majority)": {
        "lat_min": 51.220, "lat_max": 51.238,
        "lon_min": -114.462, "lon_max": -114.433,
    },
    "Sunset (Before Sunset Rd)": {
        "lat_min": 51.232, "lat_max": 51.250,
        "lon_min": -114.468, "lon_max": -114.438,
    },
    "Sunset (On/Past Sunset Rd)": {
        "lat_min": 51.245, "lat_max": 51.265,
        "lon_min": -114.468, "lon_max": -114.436,
    },
    "Fireside (Business Area)": {
        "lat_min": 51.180, "lat_max": 51.192,
        "lon_min": -114.488, "lon_max": -114.465,
    },
    "SLS Centre (SLRC)": {
        "lat_min": 51.188, "lat_max": 51.200,
        "lon_min": -114.462, "lon_max": -114.443,
    },
    "Seminary/Interpipeline": {
        "lat_min": 51.193, "lat_max": 51.210,
        "lon_min": -114.530, "lon_max": -114.505,
    },
    "Spring Hill RV/Cook Rd": {
        "lat_min": 51.222, "lat_max": 51.242,
        "lon_min": -114.440, "lon_max": -114.410,
    },
    "Monterra/Coch Lk/Camden": {
        "lat_min": 51.153, "lat_max": 51.175,
        "lon_min": -114.545, "lon_max": -114.510,
    },
}


# Shrinks bounding box checks inward to reduce edge/overlap mismatches.
BUFFER = 0.0008

# Evaluation order for detect_zone_by_coords.
# Smaller and more specific zones are listed first so they win when boxes overlap.
ZONE_PRIORITY = [
    # Specific facility
    "SLS Centre (SLRC)",
    # Fireside sub-zones (business strip before residential)
    "Fireside (Business Area)",
    "Fireside (Residential)",
    # Heritage sub-zones (shallow/near-town edge first)
    "H.Land/Heritage (Shallow)",
    "H.Land/Heritage (Majority)",
    # Sunset sub-zones (before the road first)
    "Sunset (Before Sunset Rd)",
    "Sunset (On/Past Sunset Rd)",
    # Mid-size distinct neighbourhoods
    "Glenbow",
    "Riverview/Greystone",
    "Riviera/Precedence",
    "Bow Meadows/Crawford",
    "Willows/Rivercrest/Ford",
    "Sunterra",
    "West Terrace/Pointe",
    "Cochrane Heights",
    "Riversong/BVHS",
    # Broader zones with higher overlap risk
    "West Valley/Mitford",
    "East End/Industrial",
    "Bow Ridge/Jumping Pound",
    "Downtown/Quarry",
    # Outer/far zones
    "Spring Hill RV/Cook Rd",
    "Seminary/Interpipeline",
    "Monterra/Coch Lk/Camden",
]


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


# -----------------------------------------------------------
# - Normalize text
# - Lowercase and trim spaces
# -----------------------------------------------------------
def normalize_text(text_input):
    return text_input.lower().strip()


# -----------------------------------------------------------
# - Find all matching zones
# - Return list of possible zone matches
# -----------------------------------------------------------
def detect_possible_zones(text_input):
    text = normalize_text(text_input)
    matches = []

    for zone_name, keywords in ZONE_PATTERNS.items():
        for keyword in keywords:
            if keyword in text:
                matches.append(zone_name)
                break

    return matches


# -----------------------------------------------------------
# - Detect best zone
# - Return first match, else Unknown Zone
# -----------------------------------------------------------
def detect_zone(text_input):
    matches = detect_possible_zones(text_input)

    if matches:
        return matches[0]

    return "Unknown Zone"


# -----------------------------------------------------------
# - Detect zone by GPS coordinates
# - Checks each bounding box; returns first match or None
# -----------------------------------------------------------
def detect_zone_by_coords(lat: float, lon: float) -> str | None:
    for zone_name in ZONE_PRIORITY:
        bounds = ZONE_BOUNDARIES[zone_name]
        if (bounds["lat_min"] + BUFFER <= lat <= bounds["lat_max"] - BUFFER and
                bounds["lon_min"] + BUFFER <= lon <= bounds["lon_max"] - BUFFER):
            return zone_name
    return None
