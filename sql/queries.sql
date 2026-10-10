-- =====================================================================
-- queries.sql  -  Analysis questions answered with SQL
-- Each query starts with a line "-- name: <title>". main.py splits the
-- file on those lines and runs each query separately.
-- =====================================================================

-- name: 1. Safe-water coverage per region (SDG 6.1)
-- Question: what share of each region's population is served by a WORKING, SAFE source?
SELECT
    r.name                                              AS region,        -- region name from the regions table
    r.population                                        AS population,    -- total people living there
    SUM(CASE WHEN w.is_functional = 1                                     -- count people only if the point works...
              AND w.source_type <> 'unprotected_well'                     -- ...and is a safe (improved) source
             THEN w.people_served ELSE 0 END)           AS safely_served, -- otherwise add 0
    ROUND(100.0 * SUM(CASE WHEN w.is_functional = 1
                            AND w.source_type <> 'unprotected_well'
                           THEN w.people_served ELSE 0 END)
          / r.population, 1)                            AS coverage_pct   -- 100.0 forces decimal (not integer) division
FROM regions r                                                            -- start from regions, alias "r"
LEFT JOIN water_points w ON w.region_id = r.region_id                     -- LEFT JOIN keeps regions that have no water points
GROUP BY r.region_id                                                      -- one result row per region
ORDER BY coverage_pct ASC;                                                -- worst-served regions first

-- name: 2. Broken water points that need repair
-- Question: where are the most people losing access because a point is broken?
SELECT
    r.name                 AS region,           -- region name
    COUNT(*)               AS broken_points,    -- how many broken points in that region
    SUM(w.people_served)   AS people_affected   -- how many people those broken points used to serve
FROM water_points w                             -- start from water points
JOIN regions r ON r.region_id = w.region_id     -- inner JOIN: attach the region name to each point
WHERE w.is_functional = 0                       -- keep only broken points (WHERE filters rows BEFORE grouping)
GROUP BY r.region_id                            -- total them up per region
HAVING SUM(w.people_served) > 0                 -- HAVING filters groups AFTER grouping
ORDER BY people_affected DESC;                  -- biggest problem first = repair priority list

-- name: 3. Disease rate per 1,000 people vs. water coverage
-- Question: do regions with lower safe-water coverage report more diarrhoea?
WITH coverage AS (                                                     -- CTE: a named temporary result we can reuse below
    SELECT
        r.region_id,                                                   -- key used to join later
        100.0 * SUM(CASE WHEN w.is_functional = 1
                          AND w.source_type <> 'unprotected_well'
                         THEN w.people_served ELSE 0 END)
              / r.population AS coverage_pct                           -- same coverage maths as query 1
    FROM regions r
    LEFT JOIN water_points w ON w.region_id = r.region_id
    GROUP BY r.region_id
),
yearly_cases AS (                                                      -- second CTE: total cases per region
    SELECT region_id, SUM(diarrhoea_cases) AS total_cases              -- add up all months
    FROM disease_cases
    GROUP BY region_id
)
SELECT
    r.name                                                AS region,          -- region name
    ROUND(c.coverage_pct, 1)                              AS coverage_pct,    -- safe-water coverage
    ROUND(1000.0 * y.total_cases / r.population, 2)       AS cases_per_1000,  -- normalise by population so regions compare fairly
    CASE WHEN c.coverage_pct < 50 THEN 'HIGH RISK'                            -- label each region with a simple rule
         WHEN c.coverage_pct < 80 THEN 'MEDIUM RISK'
         ELSE 'LOW RISK' END                              AS risk_band
FROM regions r
JOIN coverage     c ON c.region_id = r.region_id         -- attach coverage from the first CTE
JOIN yearly_cases y ON y.region_id = r.region_id         -- attach case totals from the second CTE
ORDER BY cases_per_1000 DESC;                            -- most affected first

-- name: 4. Month-over-month change in cases (window function LAG)
-- Question: is the situation getting better or worse each month?
SELECT
    r.name                                             AS region,         -- region name
    d.month                                            AS month,          -- the month being reported
    d.diarrhoea_cases                                  AS cases,          -- this month's cases
    LAG(d.diarrhoea_cases) OVER (                      -- LAG looks at the PREVIOUS row...
        PARTITION BY d.region_id                       -- ...inside the same region only...
        ORDER BY d.month)                              AS prev_month,     -- ...ordered by month
    d.diarrhoea_cases - LAG(d.diarrhoea_cases) OVER (
        PARTITION BY d.region_id ORDER BY d.month)     AS change          -- positive = getting worse, negative = improving
FROM disease_cases d
JOIN regions r ON r.region_id = d.region_id            -- attach region name
ORDER BY r.name, d.month;                              -- group visually by region, then by time

-- name: 5. Rank regions inside each state (window function RANK)
-- Question: which region is worst-off in each state, so the state knows where to act first?
WITH coverage AS (
    SELECT
        r.region_id, r.name, r.state,                                  -- identifiers we want in the output
        100.0 * SUM(CASE WHEN w.is_functional = 1
                          AND w.source_type <> 'unprotected_well'
                         THEN w.people_served ELSE 0 END)
              / r.population AS coverage_pct                           -- same coverage maths again
    FROM regions r
    LEFT JOIN water_points w ON w.region_id = r.region_id
    GROUP BY r.region_id
)
SELECT
    state,                                                             -- the state
    name                                     AS region,                -- the region
    ROUND(coverage_pct, 1)                   AS coverage_pct,          -- its coverage
    RANK() OVER (PARTITION BY state                                    -- restart the ranking for every state
                 ORDER BY coverage_pct ASC)  AS priority_rank          -- rank 1 = lowest coverage = act here first
FROM coverage
ORDER BY state, priority_rank;                                         -- show each state's priority list in order
