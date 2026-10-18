-- SQLite schema for the 2025/26 A&E monthly data, as a small star schema.
--   dim_month, dim_org            -> descriptive attributes
--   fact_ae_type_month            -> one row per organisation, month and A&E type, in long format
--   fact_org_month                -> measures that the source does not split by A&E type
--   published_totals              -> NHS England's own TOTAL rows, kept only for reconciliation
-- CHECK constraints make the database refuse impossible numbers.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_ae_type_month;
DROP TABLE IF EXISTS published_totals;
DROP TABLE IF EXISTS fact_ae_type_month;
DROP TABLE IF EXISTS fact_org_month;
DROP TABLE IF EXISTS dim_org;
DROP TABLE IF EXISTS dim_month;

CREATE TABLE dim_month (
    month_start    TEXT PRIMARY KEY,                 -- ISO date of the 1st, e.g. '2025-06-01'
    month_label    TEXT NOT NULL,                    -- 'Jun 2025'
    days_in_month  INTEGER NOT NULL CHECK (days_in_month BETWEEN 28 AND 31),
    source_file   TEXT NOT NULL                      -- which CSV this month came from
);

CREATE TABLE dim_org (
    org_code              TEXT PRIMARY KEY,          -- the stable key (names changed for 4 orgs)
    org_name              TEXT NOT NULL,             -- as published, most recent month
    org_name_display      TEXT NOT NULL,             -- tidied for charts
    region                TEXT NOT NULL,
    has_type1             INTEGER NOT NULL CHECK (has_type1 IN (0, 1)),
    is_children_or_womens INTEGER NOT NULL CHECK (is_children_or_womens IN (0, 1))
);

CREATE TABLE fact_ae_type_month (
    org_code             TEXT NOT NULL REFERENCES dim_org (org_code),
    month_start          TEXT NOT NULL REFERENCES dim_month (month_start),
    ae_type              TEXT NOT NULL CHECK (ae_type IN ('Type 1', 'Type 2', 'Other')),
    attendances          INTEGER NOT NULL CHECK (attendances >= 0),
    booked_attendances   INTEGER NOT NULL CHECK (booked_attendances >= 0),
    over_4hrs            INTEGER NOT NULL CHECK (over_4hrs >= 0),
    booked_over_4hrs     INTEGER NOT NULL CHECK (booked_over_4hrs >= 0),
    emergency_admissions INTEGER NOT NULL CHECK (emergency_admissions >= 0),
    PRIMARY KEY (org_code, month_start, ae_type),
    CHECK (over_4hrs <= attendances),
    CHECK (booked_over_4hrs <= booked_attendances)
);

CREATE TABLE fact_org_month (
    org_code                   TEXT NOT NULL REFERENCES dim_org (org_code),
    month_start                TEXT NOT NULL REFERENCES dim_month (month_start),
    dta_4_to_12h               INTEGER NOT NULL CHECK (dta_4_to_12h >= 0),
    dta_12h_plus               INTEGER NOT NULL CHECK (dta_12h_plus >= 0),
    other_emergency_admissions INTEGER NOT NULL CHECK (other_emergency_admissions >= 0),
    PRIMARY KEY (org_code, month_start)
);

-- Wide copy of the 12 published TOTAL rows (clean column names, same as the wide cleaned data).
CREATE TABLE published_totals (
    month_start TEXT PRIMARY KEY REFERENCES dim_month (month_start),
    t1_attendances INTEGER, t1_booked_attendances INTEGER, t1_over_4hrs INTEGER, t1_booked_over_4hrs INTEGER, t1_emergency_admissions INTEGER,
    t2_attendances INTEGER, t2_booked_attendances INTEGER, t2_over_4hrs INTEGER, t2_booked_over_4hrs INTEGER, t2_emergency_admissions INTEGER,
    oth_attendances INTEGER, oth_booked_attendances INTEGER, oth_over_4hrs INTEGER, oth_booked_over_4hrs INTEGER, oth_emergency_admissions INTEGER,
    dta_4_to_12h INTEGER, dta_12h_plus INTEGER, other_emergency_admissions INTEGER
);

CREATE INDEX ix_fact_type_month ON fact_ae_type_month (ae_type, month_start);
