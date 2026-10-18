-- Q5. How much does each trust's Type 1 performance move during the year? (best month vs worst month)
-- Why: a trust that is steady and one that swings widely can have the same annual average.
-- Attendances include booked appointments (see Q1).
WITH trust_month AS (
    SELECT  org_code, org_name, month_label, month_start,
            100.0 * (1 - 1.0 * (over_4hrs + booked_over_4hrs) / (attendances + booked_attendances)) AS pct_within_4h
    FROM    v_ae_type_month
    WHERE   ae_type = 'Type 1' AND attendances + booked_attendances > 0 AND is_children_or_womens = 0
)
SELECT  org_code, org_name,
        ROUND(MIN(pct_within_4h), 1)                    AS worst_month_pct,
        ROUND(MAX(pct_within_4h), 1)                    AS best_month_pct,
        ROUND(MAX(pct_within_4h) - MIN(pct_within_4h), 1) AS spread_pts
FROM    trust_month
GROUP BY org_code, org_name
ORDER BY spread_pts DESC;
