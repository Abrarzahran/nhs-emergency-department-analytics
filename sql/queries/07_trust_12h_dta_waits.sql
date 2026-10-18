-- Q7. Trusts with the most patients waiting over 12 hours from decision to admit (DTA) to admission.
-- Counts only, deliberately. NHS England's definitions (A3/A4) measure the wait from the decision to admit (or the end of
-- A&E treatment, if later) to admission, not split by A&E type, and the wait for a patient transferred to another provider
-- ends when they are collected. The emergency-admission counts (B1i-iii) only include patients admitted to the same provider.
-- The two measures therefore do not describe the same group of patients, so a "waits per admission" ratio is not a true
-- proportion and is not computed here. Larger trusts will naturally have more waits: these counts are not adjusted for size.
SELECT  o.org_code, o.org_name_display AS org_name, o.region,
        SUM(f.dta_12h_plus)                         AS over_12h_dta_waits,
        SUM(f.dta_4_to_12h)                         AS dta_waits_4_to_12h
FROM    fact_org_month f
JOIN    dim_org o USING (org_code)
GROUP BY o.org_code, o.org_name_display, o.region
ORDER BY over_12h_dta_waits DESC
LIMIT 15;
