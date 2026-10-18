-- Q1. National monthly attendances and 4-hour performance, separately for each A&E type.
-- Why: the three types are different services (major A&E vs single-specialty vs "other" departments),
--      so each gets its own line. There is deliberately no "all types" row here.
-- Method: SUM counts first, divide after. Attendances include booked appointment attendances, as NHS England's
--         published headline does (reconciled in docs/OFFICIAL_RECONCILIATION.md and tests/test_official_reconciliation.py).
SELECT  month_label,
        ae_type,
        SUM(attendances + booked_attendances)                                        AS attendances,
        ROUND(1.0 * SUM(attendances + booked_attendances) / days_in_month, 0)        AS attendances_per_day,
        ROUND(100.0 * (1 - 1.0 * SUM(over_4hrs + booked_over_4hrs)
                         / NULLIF(SUM(attendances + booked_attendances), 0)), 1)     AS pct_within_4h,
        SUM(emergency_admissions)                                                    AS emergency_admissions
FROM    v_ae_type_month
GROUP BY month_start, month_label, days_in_month, ae_type
ORDER BY ae_type, month_start;
