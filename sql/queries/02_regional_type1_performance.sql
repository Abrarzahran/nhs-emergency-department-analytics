-- Q2. Type 1 four-hour performance by NHS England region, full year, with a rank.
-- Why: regions are compared on Type 1 only, so a region with many urgent-care-centre (Other) attendances
--      is not flattered by them. RANK() is a window function: it ranks rows without collapsing them.
-- Attendances include booked appointments (see Q1).
WITH region_year AS (
    SELECT  region,
            SUM(attendances + booked_attendances) AS attendances,
            SUM(over_4hrs + booked_over_4hrs)     AS over_4hrs
    FROM    v_ae_type_month
    WHERE   ae_type = 'Type 1'
    GROUP BY region
)
SELECT  RANK() OVER (ORDER BY 1.0 * over_4hrs / attendances ASC) AS rank_best_first,
        region,
        attendances,
        ROUND(100.0 * (1 - 1.0 * over_4hrs / attendances), 1)   AS pct_within_4h
FROM    region_year
ORDER BY rank_best_first;
