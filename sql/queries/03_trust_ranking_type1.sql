-- Q3. Trust league table: Type 1 only, full year, excluding children's / women's providers.
-- Why Type 1 only: it is the only type every general acute trust reports, so it is the like-for-like set.
-- Why exclude children's/women's: different case-mix (flagged in dim_org by a name heuristic).
-- Attendances include booked appointments (see Q1).
SELECT  RANK() OVER (ORDER BY 1.0 * SUM(over_4hrs + booked_over_4hrs) / SUM(attendances + booked_attendances) ASC) AS rank_best_first,
        org_code,
        org_name,
        region,
        SUM(attendances + booked_attendances)                                                   AS type1_attendances,
        ROUND(100.0 * (1 - 1.0 * SUM(over_4hrs + booked_over_4hrs)
                         / SUM(attendances + booked_attendances)), 1)                           AS pct_within_4h
FROM    v_ae_type_month
WHERE   ae_type = 'Type 1'
  AND   is_children_or_womens = 0
GROUP BY org_code, org_name, region
HAVING  SUM(attendances + booked_attendances) > 0
ORDER BY rank_best_first, org_name;
