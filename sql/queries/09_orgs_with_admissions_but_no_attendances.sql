-- Q9. Data-quality probe: organisations that report emergency admissions but no A&E attendances at all.
-- These are not emergency departments (e.g. specialist or mental-health providers); they must not appear
-- in any 4-hour performance ranking, because performance is undefined with zero attendances.
SELECT  o.org_code, o.org_name_display AS org_name, o.region,
        SUM(f.other_emergency_admissions)                          AS other_emergency_admissions,
        (SELECT SUM(attendances) FROM fact_ae_type_month t WHERE t.org_code = o.org_code) AS total_ae_attendances
FROM    fact_org_month f
JOIN    dim_org o USING (org_code)
GROUP BY o.org_code, o.org_name_display, o.region
HAVING  total_ae_attendances = 0 AND other_emergency_admissions > 0
ORDER BY other_emergency_admissions DESC;
