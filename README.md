# TAXI4U Fare System

## Project Purpose
Zone-based taxi fare calculator system.

This system:
- Maps input text → zones
- Validates trip data
- Calculates fare based on predefined matrix
- Applies extra stop and waiting rules

---

## Current Features

### 1. Fare Engine (`calculator.py`)
- Base fare lookup from matrix
- Extra stop fee ($4 per stop)
- Waiting fee ($0.50/min after 4 min)
- Total fare calculation

### 2. Zone Mapper (`zone_mapper.py`)
- Converts text input into zones using keyword matching
- Returns "Unknown Zone" if no match found

### 3. Trip Flow
1. Detect zones from input text
2. Prepare trip data
3. Validate trip
4. Confirm trip
5. Calculate fare

---

## File Structure

TAXI4U/
│
├── fares.json
├── calculator.py
├── zone_mapper.py
├── README.md
├── structure.txt

---

## Important Rules

- No manual input inside core logic
- All calculations must come from structured data
- Unknown zones must be handled before calculation

---

## Next Steps (Planned)

- Improve zone detection (more keywords / accuracy)
- Replace keyword detection with GPS or address-based mapping
- Add API layer (FastAPI)
- Add frontend or driver interface
- Add database support

---

## Environment

- Python only (no venv required yet)
- venv will be introduced when external libraries are added

---

## How to Run

python calculator.py

---

## Notes

This is a modular system:
- Each part is independent
- Designed for future app integration