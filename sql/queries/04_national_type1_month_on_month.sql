-- Q4. Month-on-month change in national Type 1 performance, using LAG().
-- Why: shows seasonality without eyeballing a chart. Change is in percentage points and not percent.
-- Attendances include booked appointments (see Q1).
WITH monthly AS (
    SELECT  month_start, month_label, days_in_month,
            SUM(attendances + booked_attendances) AS attendances,
            100.0 * (1 - 1.0 * SUM(over_4hrs + booked_over_4hrs) / SUM(attendances + booked_attendances)) AS pct_within_4h
    FROM    v_ae_type_month
    WHERE   ae_type = 'Type 1'
    GROUP BY month_start, month_label, days_in_month
)
SELECT  month_label,
        ROUND(1.0 * attendances / days_in_month, 0)                                   AS attendances_per_day,
        ROUND(pct_within_4h, 1)                                                      AS pct_within_4h,
        ROUND(pct_within_4h - LAG(pct_within_4h) OVER (ORDER BY month_start), 1)    AS change_vs_prev_month_pts
FROM    monthly
ORDER BY month_start;
