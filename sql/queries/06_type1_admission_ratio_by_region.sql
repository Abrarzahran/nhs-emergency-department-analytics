-- Q6. Of Type 1 attendances, how many ended as an emergency admission via A&E, by region?
-- Denominator includes booked-appointment attendances (NHS England's own "% of Type 1 attendances resulting
-- in admission" reconciles only on that basis as set out in docs/OFFICIAL_RECONCILIATION.md).
-- This is an admission ratio and not a clinical conversion rate. It reflects case mix,
-- ambulatory/same-day-care models and local recording, so treat differences as prompts for questions.
SELECT  region,
        SUM(attendances + booked_attendances)                                       AS type1_attendances,
        SUM(emergency_admissions)                                                   AS type1_emergency_admissions,
        ROUND(100.0 * SUM(emergency_admissions) / SUM(attendances + booked_attendances), 1) AS admissions_per_100_attendances
FROM    v_ae_type_month
WHERE   ae_type = 'Type 1'
GROUP BY region
ORDER BY admissions_per_100_attendances DESC;
