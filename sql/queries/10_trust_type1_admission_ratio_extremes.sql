-- Q10. Type 1 admission ratio by trust: lowest and highest 5 (children's/women's excluded).
-- Denominator includes booked-appointment attendances (see Q6).
-- Purpose: a sanity probe. A very low ratio can reflect how a trust records admissions (for example same-day
-- emergency care not counted as an admission), not better or worse care. It should not be read as a quality score.
WITH t AS (
    SELECT  org_code, org_name,
            100.0 * SUM(emergency_admissions) / SUM(attendances + booked_attendances) AS admissions_per_100_attendances,
            ROW_NUMBER() OVER (ORDER BY 1.0 * SUM(emergency_admissions) / SUM(attendances + booked_attendances) ASC)  AS rn_low,
            ROW_NUMBER() OVER (ORDER BY 1.0 * SUM(emergency_admissions) / SUM(attendances + booked_attendances) DESC) AS rn_high
    FROM    v_ae_type_month
    WHERE   ae_type = 'Type 1' AND is_children_or_womens = 0
    GROUP BY org_code, org_name
    HAVING  SUM(attendances + booked_attendances) > 0
)
SELECT  CASE WHEN rn_low <= 5 THEN 'lowest 5' ELSE 'highest 5' END AS group_label,
        org_code, org_name, ROUND(admissions_per_100_attendances, 1) AS admissions_per_100_attendances
FROM    t
WHERE   rn_low <= 5 OR rn_high <= 5
ORDER BY admissions_per_100_attendances;
