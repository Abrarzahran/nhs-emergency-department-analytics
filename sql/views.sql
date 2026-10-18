-- One convenience view: the fact table joined to its dimensions.
-- Rates such as four-hour performance are not stored. They are always computed
-- from summed counts at whatever grain a query needs (see docs/DECISIONS.md, decision 4).

DROP VIEW IF EXISTS v_ae_type_month;
CREATE VIEW v_ae_type_month AS
SELECT  f.org_code,
        o.org_name_display      AS org_name,
        o.region,
        o.has_type1,
        o.is_children_or_womens,
        f.month_start,
        m.month_label,
        m.days_in_month,
        f.ae_type,
        f.attendances,
        f.over_4hrs,
        f.booked_attendances,
        f.booked_over_4hrs,
        f.emergency_admissions
FROM    fact_ae_type_month f
JOIN    dim_org   o ON o.org_code    = f.org_code
JOIN    dim_month m ON m.month_start = f.month_start;
