"""Central configuration: paths, the expected raw schema and the column mapping.

Everything that depends on the *exact wording* of the NHS England column headers
lives here, so if NHS England renames a column there is exactly one place to fix.
The 22 headers below were read directly from the 12 monthly CSV files (April 2025
to March 2026); `tests/test_schema.py` re-checks them on every test run.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_PATH = PROCESSED_DIR / "ae_2025_26.sqlite"
SQL_DIR = PROJECT_ROOT / "sql"

SOURCE_URL = (
    "https://www.england.nhs.uk/statistics/statistical-work-areas/"
    "ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2025-26/"
)

# Raw schema, exactly as published, including the source's own typo "hs"
ID_COLUMNS = ["Period", "Org Code", "Parent Org", "Org name"]

# A&E type -> {measure -> raw column name}
# "Other" is the source's "Other A&E Department" (see docs/DATA_DICTIONARY.md).
TYPE_COLUMNS = {
    "Type 1": {
        "attendances": "A&E attendances Type 1",
        "booked_attendances": "A&E attendances Booked Appointments Type 1",
        "over_4hrs": "Attendances over 4hrs Type 1",
        "booked_over_4hrs": "Attendances over 4hrs Booked Appointments Type 1",
        "emergency_admissions": "Emergency admissions via A&E - Type 1",
    },
    "Type 2": {
        "attendances": "A&E attendances Type 2",
        "booked_attendances": "A&E attendances Booked Appointments Type 2",
        "over_4hrs": "Attendances over 4hrs Type 2",
        "booked_over_4hrs": "Attendances over 4hrs Booked Appointments Type 2",
        "emergency_admissions": "Emergency admissions via A&E - Type 2",
    },
    "Other": {
        "attendances": "A&E attendances Other A&E Department",
        "booked_attendances": "A&E attendances Booked Appointments Other Department",
        "over_4hrs": "Attendances over 4hrs Other Department",
        "booked_over_4hrs": "Attendances over 4hrs Booked Appointments Other Department",
        "emergency_admissions": "Emergency admissions via A&E - Other A&E department",
    },
}
AE_TYPES = list(TYPE_COLUMNS)  # ["Type 1", "Type 2", "Other"]
MEASURES = list(next(iter(TYPE_COLUMNS.values())))

# Measures that the source does not split by A&E type, with one value per organisation
ORG_LEVEL_COLUMNS = {
    "dta_4_to_12h": "Patients who have waited 4-12 hs from DTA to admission",
    "dta_12h_plus": "Patients who have waited 12+ hrs from DTA to admission",
    "other_emergency_admissions": "Other emergency admissions",
}

TYPE_KEY = {"Type 1": "t1", "Type 2": "t2", "Other": "oth"}  # "oth" (not "other") so it can never clash with org-level other_emergency_admissions

# raw column name -> clean "wide" column name, e.g. "A&E attendances Type 1" -> "t1_attendances"
RAW_TO_CLEAN = {
    raw: f"{TYPE_KEY[t]}_{m}" for t, cols in TYPE_COLUMNS.items() for m, raw in cols.items()
}
RAW_TO_CLEAN.update({raw: clean for clean, raw in ORG_LEVEL_COLUMNS.items()})

RAW_NUMERIC_COLUMNS = list(RAW_TO_CLEAN)
EXPECTED_RAW_COLUMNS = ID_COLUMNS + RAW_NUMERIC_COLUMNS  # 4 + 18 = 22
CLEAN_NUMERIC_COLUMNS = list(RAW_TO_CLEAN.values())
assert len(set(CLEAN_NUMERIC_COLUMNS)) == len(CLEAN_NUMERIC_COLUMNS), "clean column names must be unique"

# Reporting window
FIRST_MONTH = "2025-04-01"
LAST_MONTH = "2026-03-01"
EXPECTED_MONTHS = 12

REGION_MAP = {
    "NHS ENGLAND EAST OF ENGLAND": "East of England",
    "NHS ENGLAND LONDON": "London",
    "NHS ENGLAND MIDLANDS": "Midlands",
    "NHS ENGLAND NORTH EAST AND YORKSHIRE": "North East and Yorkshire",
    "NHS ENGLAND NORTH WEST": "North West",
    "NHS ENGLAND SOUTH EAST": "South East",
    "NHS ENGLAND SOUTH WEST": "South West",
}

# Heuristic used only to flag paediatric and women's providers that report Type 1
# activity but have a different case mix from general acute hospitals.
SPECIALIST_NAME_PATTERN = r"CHILDREN|WOMEN"
