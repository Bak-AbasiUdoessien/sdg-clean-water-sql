-- =====================================================================
-- schema.sql  -  Database structure for the Clean Water & Health Tracker
-- SDG 6 (Clean Water & Sanitation) + SDG 3 (Good Health & Well-being)
-- =====================================================================

-- Delete the tables if they already exist, so the script can be re-run safely.
-- Children are dropped before parents so foreign keys never point at nothing.
DROP TABLE IF EXISTS disease_cases;   -- monthly illness counts (child of regions)
DROP TABLE IF EXISTS water_points;    -- wells, boreholes, taps (child of regions)
DROP TABLE IF EXISTS regions;         -- the parent table every other table refers to

-- One row per region (district / local government area).
CREATE TABLE regions (
    region_id   INTEGER PRIMARY KEY,          -- unique number that identifies the region
    name        TEXT    NOT NULL UNIQUE,      -- region name; NOT NULL = required, UNIQUE = no duplicates
    state       TEXT    NOT NULL,             -- the larger state/province the region belongs to
    population  INTEGER NOT NULL CHECK (population > 0)  -- CHECK rejects zero or negative populations
);

-- One row per physical water source.
CREATE TABLE water_points (
    point_id       INTEGER PRIMARY KEY,                       -- unique id for the water point
    region_id      INTEGER NOT NULL REFERENCES regions(region_id), -- foreign key: must match a real region
    source_type    TEXT    NOT NULL
                   CHECK (source_type IN ('borehole', 'protected_well', 'piped_tap', 'unprotected_well')), -- only allowed values
    is_functional  INTEGER NOT NULL CHECK (is_functional IN (0, 1)), -- SQLite has no BOOLEAN, so 1 = working, 0 = broken
    people_served  INTEGER NOT NULL CHECK (people_served >= 0)       -- how many people rely on this point
);

-- One row per region per month: reported cases of water-borne illness.
CREATE TABLE disease_cases (
    region_id        INTEGER NOT NULL REFERENCES regions(region_id), -- which region reported the cases
    month            TEXT    NOT NULL,                               -- month stored as 'YYYY-MM' text (sorts correctly)
    diarrhoea_cases  INTEGER NOT NULL CHECK (diarrhoea_cases >= 0),  -- number of diarrhoea cases that month
    PRIMARY KEY (region_id, month)                                   -- composite key: one report per region per month
);

-- Indexes make lookups by region faster once the tables get large.
CREATE INDEX idx_water_region   ON water_points(region_id);   -- speeds up JOINs from water_points to regions
CREATE INDEX idx_disease_region ON disease_cases(region_id);  -- speeds up JOINs from disease_cases to regions
