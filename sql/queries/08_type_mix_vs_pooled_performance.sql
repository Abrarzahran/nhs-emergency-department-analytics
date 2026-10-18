-- Q8. Why not rank on the pooled figure? This compares pooled "all types" performance with Type 1 performance by region.
-- NHS England does publish a pooled all-department percentage, and it is a legitimate national headline. It is not
-- a like-for-like basis for comparing areas, because it blends in "Other" departments (different services), so an area's
-- pooled figure depends on how many "Other" attendances it happens to have. This query makes that visible.
-- Attendances include booked appointments (see Q1).
WITH r AS (
    SELECT  region,
            SUM(CASE WHEN ae_type = 'Type 1' THEN attendances + booked_attendances END) AS t1_att,
            SUM(CASE WHEN ae_type = 'Type 1' THEN over_4hrs + booked_over_4hrs END)     AS t1_over,
            SUM(attendances + booked_attendances)                                       AS all_att,
            SUM(over_4hrs + booked_over_4hrs)                                           AS all_over
    FROM    v_ae_type_month
    GROUP BY region
)
SELECT  region,
        ROUND(100.0 * t1_att / all_att, 1)                       AS type1_share_of_attendances_pct,
        ROUND(100.0 * (1 - 1.0 * t1_over  / t1_att),  1)         AS type1_pct_within_4h,
        ROUND(100.0 * (1 - 1.0 * all_over / all_att), 1)         AS pooled_all_types_pct_within_4h,
        ROUND(100.0 * (1 - 1.0 * all_over / all_att)
            - 100.0 * (1 - 1.0 * t1_over  / t1_att), 1)          AS pooled_minus_type1_pts
FROM    r
ORDER BY type1_share_of_attendances_pct;
