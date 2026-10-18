# Design decisions

This file records the main choices made in the code and the analysis, the reason for each, and where the evidence is in the repository.

## 1. Key everything on `org_code`, not on organisation name

Four organisations were renamed during the year: RA2 Royal Surrey, RRF Wrightington Wigan and Leigh, RWH East and North Herts, and A5D4Q NEMS. Grouping by name would split each into two organisations and drop months from both. `dim_org` keeps the most recent name. The number of distinct names per code was checked before the key was chosen. Evidence: `validate.warn_renamed_orgs` and `tests/test_clean.py::test_dim_org_uses_most_recent_name`.

## 2. Identify the TOTAL row by `Org Code`, not by `Period`

In 11 files the TOTAL row has `Period` set to `TOTAL`. In the February 2026 file it carries `MSitAE-FEBRUARY-2026`. Filtering on `Period` would leave a national total among the organisation rows and double count every February figure. Evidence: `tests/test_clean.py::test_total_row_is_removed_whatever_its_period_says`, which covers both forms.

The TOTAL rows are kept as `published_totals` and used for the reconciliation in decision 3.

## 3. Reconcile the organisation rows to the published totals

The organisation rows should add up to NHS England's TOTAL row. All 18 numeric columns match in all 12 months, with a largest difference of 0. This is the main check that parsing, joining and type conversion neither lost nor duplicated rows. Evidence: `validate.check_reconciles_to_published_totals`, and a test that changes one count by 1 and confirms the check fails.

## 4. Calculate rates from summed counts

Averaging each trust's percentage gives a unit with 10 attendances the same weight as one with 1,000. The example in `tests/test_metrics.py` has two units at 50% and 90%, which average to 70%, while the volume-weighted figure is 89.6%. Rates are therefore not stored in the database. Each query sums the over-four-hour counts and the attendances first and divides last, using `NULLIF` to avoid division by zero.

## 5. Booked appointments are included in the headline rates, with a switch

The data have separate booked appointment columns for attendances and for over-four-hour waits.

The first version excluded them by default, as an assumption. A comparison with NHS England's published commentaries showed otherwise. Including booked attendances reproduces the published Type 1 percentage in 8 of 8 months and the all-department percentage in 7 of 8, with the eighth differing by 0.1. Excluding them misses every month by 0.2 to 0.4 points. The published percentage of Type 1 attendances resulting in admission also matches only when booked attendances are in the denominator. The table is in [OFFICIAL_RECONCILIATION.md](OFFICIAL_RECONCILIATION.md).

The default, the SQL queries, the findings and the documentation were then changed to include booked attendances in both the numerator and the denominator. An unbooked-only option remains. Nationally the two bases differ by 0.3 points, but for individual trusts the difference can be large. East Sussex Healthcare differs by 7.5 points, because booked attendances are 18% of its Type 1 activity, and nine trusts differ by more than 1 point.

Version 5.0 of the definitions document defines unplanned attendances, which exclude booked appointments, in A1i to A1iii, and attended booked appointments as a separate series in A1iv to A1vi. It defines no percentage and no combined total. It has no over-four-hour items for booked appointments, because the booked over-four-hour columns in the CSV files postdate it. The booked-inclusive basis therefore rests on the reconciliation with published figures and not on the definitions document. This is stated in [DEFINITIONS_CROSSWALK.md](DEFINITIONS_CROSSWALK.md).

## 6. Do not pool A&E types, and compare trusts on Type 1 only

Type 1 is a major emergency department, Type 2 is a single specialty service, and Other A&E department covers urgent treatment centres and similar services. Over the year Type 1 performance is about 61%, against about 95 to 98% a month for the other types. A pooled figure mostly reflects how many urgent treatment centre attendances an area has.

SQL query 08 shows that pooling adds 12.3 to 15.1 points to each region's figure. NHS England does publish a pooled all-department figure, which is reasonable nationally but is not a like-for-like basis for comparing areas. The dashboard has a panel that shows the same effect. The trust ranking filters on `ae_type = 'Type 1'`, and `test_trust_ranking_contains_only_organisations_with_type1_activity` confirms that a Type 2 only provider such as Moorfields cannot appear.

Under the definitions document, a patient streamed from Type 1 to a co-located Type 3 service counts as one Type 3 attendance, and a patient streamed to same-day emergency care on arrival is not an A&E attendance. These are Examples A to D and FAQ 12. Trusts with different streaming arrangements therefore have different Type 1 populations. Type 1 is the best like-for-like group available but not a perfect one, and the data cannot adjust for this.

The fact table is in long format, so every query has to state which `ae_type` it uses.

## 7. Exclude children's and women's trusts from the ranking by default

Paediatric and women's departments report Type 1 activity, but their case mix differs from general acute trusts. Three Type 1 providers are affected, which are Alder Hey, Sheffield Children's and Birmingham Women's and Children's. That leaves 118 trusts. Liverpool Women's reports Type 2 only.

The flag is a name match on `CHILDREN|WOMEN`, stored as `dim_org.is_children_or_womens`, and it is a visible checkbox in the dashboard. It is based on the name alone, so it would miss a specialist hospital whose name has neither word.

## 8. Two fact tables, because decision-to-admit waits are not split by A&E type

The 4 to 12 hour and over 12 hour decision-to-admit counts, and other emergency admissions, are one value per organisation-month. They are held in `fact_org_month`. Putting them in the per-type table would create a split that the source does not provide.

## 9. SQLite with constraints, opened read-only by the dashboard

The schema has `CHECK` constraints, including over-four-hour counts not exceeding attendances, and primary keys, foreign keys and an `ae_type IN (...)` constraint. `tests/test_database.py` inserts invalid rows and expects an `IntegrityError`. The dashboard opens the file with `mode=ro`, so a bug or an unusual filter value cannot change the data.

SQLite was chosen because the task is a small analytical store with joins, constraints and window functions, and SQLite needs no server.

## 10. Parameterised SQL

Filter values such as regions, dates and trust codes are passed as bound `?` parameters. The only dynamic SQL text is a list of `?` placeholders for `IN` clauses.

## 11. Attendances per day in the trend charts

February has 28 days and the other months have 30 or 31, so monthly totals make February look quiet. `dim_month` stores the days in each month, and the per-day view is the default.

## 12. Unusual values are flagged and not changed

- 332 organisation-months have more over-12-hour waits than 4 to 12 hour waits.
- Type 1 admission ratios range from 8.9 to 57.0 per 100 attendances between trusts.
- Some trusts show over-12-hour waits that are a large share of their reported admissions.

It is not known whether these are real or reflect recording differences, and changing published figures would be fabrication. They appear as warnings in `validation_report.csv` and as caveats in the dashboard, and the admission ratio is not presented as a quality measure.

An earlier version also showed 12-hour waits per 1,000 emergency admissions. The definitions document showed that this compared different groups. Decision-to-admit waits in A3 and A4 include patients transferred to another provider, whose wait ends when they are collected. The admission counts in B1i to B1iii include only patients admitted to the same provider. The ratio was removed, and trusts are ranked on over-12-hour wait counts, with a note that the counts are not adjusted for size.

## 13. A duplicated column name found during development

The first column mapping gave two raw columns the same clean name, `other_emergency_admissions`. One was the Other A&E department admissions and the other was the organisation-level Other emergency admissions. pandas did not raise an error. It produced a table with 25 columns instead of the expected 23, and this was noticed from the printed shape. The reconciliation check did not catch it, because both copies came from the same source.

The prefix for the A&E type was renamed to `oth_`, `config.py` now asserts that the clean names are unique, and two tests were added, `test_clean_column_names_are_unique` and `test_cleaned_table_has_no_duplicate_columns`. Structure therefore needs checking as well as totals.

## 14. Raw data and generated files are kept apart

An early manifest was written to `data/raw/` as a `.csv` file, and the next run tried to load it as data. It is now `data/MANIFEST.csv`. The loader also stops if any CSV in `data/raw/` has an unexpected header.

## 15. Read everything as text, then convert with `errors="raise"`

A stray `n/a`, `-` or `*` would otherwise become NaN or 0 and change totals without warning. Every numeric cell in these files is a clean integer, but the pipeline stops if a future file is not.

## Limitations

- The analysis is descriptive. There are no case mix, staffing, bed or ambulance data, so it makes no causal claims about why trusts differ.
- It covers one year of monthly data with no time series modelling. The rise of 4.7 points into March 2026 is reported and not explained.
- The definitions were checked against version 5.0 of NHS England's definitions document, with gaps. Department types, attendances, the four-hour counting rule, the decision-to-admit bands and other emergency admissions are confirmed. The headline percentage, the booked over-four-hour columns, the admission ratio, any newer definitions version and the data licence are not established by that document. See [DEFINITIONS_CROSSWALK.md](DEFINITIONS_CROSSWALK.md).
- Three small differences from the published commentaries fall in months that were reported as revised. The cause is unconfirmed. See [REVISIONS.md](REVISIONS.md).
- There are no uncertainty estimates. Monthly percentages for small trusts can vary widely, and the ranking has no confidence intervals.
- The children's and women's flag is based on the name, as described in decision 7.

## Possible extensions

- Find a current NHS England statistical note that defines the headline percentage and the booked over-four-hour columns, and record the revision dates in `docs/REVISIONS.md`.
- Add Wilson confidence intervals to monthly trust percentages, and a funnel plot for fairer trust comparison.
- Add earlier years, which use the same schema, for year-on-year comparison, and join ICB or population data for per capita context.
