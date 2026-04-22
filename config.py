import os

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "TAXI4U-FareCalculator/1.0"}

OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
TAXI4U_DEV = os.getenv("TAXI4U_DEV", "").lower() in {"1", "true", "yes", "on"}
