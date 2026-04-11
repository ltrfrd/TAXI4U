# -----------------------------------------------------------
# - Zone Mapper (Improved Version)
# - Converts raw text/location input into a mapped zone
# -----------------------------------------------------------

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
    "Fireside Residential": [
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