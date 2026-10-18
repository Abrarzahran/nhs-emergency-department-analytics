# Data dictionary

Source: NHS England, A&E Attendances and Emergency Admissions 2025-26, monthly provider-level CSV files for April 2025 to March 2026. The release page is https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2025-26/.

## Verification status

The column meanings below were checked against NHS England's A&E Attendances and Emergency Admissions Monthly Return Definitions, version 5.0, August 2020. References such as A1i or B1iv are to sections of that document. The item-by-item comparison is in [DEFINITIONS_CROSSWALK.md](DEFINITIONS_CROSSWALK.md).

| Aspect | Status |
|---|---|
| The 22 column names, the row structure, and the organisation rows adding up to the published TOTAL row | Verified from the files by the schema tests and the validation checks. |
| Type 1, Type 2 and Other A&E department. Other A&E department is Type 3, which covers urgent treatment centres and the minor injury units, urgent care centres and walk-in centres that still report as Type 3 | Confirmed by definitions A1i to A1iii and the A&E Activity section. |
| Attendances are unplanned and exclude booked appointments, which form a separate series | Confirmed by definitions A1i to A1vi. |
| A wait over four hours means a total time in A&E of 04:00:01 or longer | Confirmed by definition A2. |
| Decision-to-admit bands: 4 to 12 hours is 04:00:01 to 12:00:00 inclusive and over 12 hours is 12:00:01 or longer | Confirmed by definitions A3 and A4. |
| Other emergency admissions are emergency admissions that did not come through an A&E department of the same provider | Confirmed by definition B1iv. |
| The headline four-hour percentage and its inclusion of booked appointments | Not defined in version 5.0. The project basis is the match with NHS England's published monthly figures, described in [OFFICIAL_RECONCILIATION.md](OFFICIAL_RECONCILIATION.md). This is evidence, not a definition. |
| The separate booked appointment over-four-hour columns | Not defined in version 5.0, which predates them. |
| Whether a newer definitions version exists | The NHS England A&E statistics page was reported to list version 5.0 as the current document. The page has not been re-checked as part of this documentation. |
| Which monthly files were revised | See [REVISIONS.md](REVISIONS.md). Revision dates are unverified. |
| Data licence | The definitions document has no licence statement. The licensing basis is in [../NOTICE.md](../NOTICE.md). |

## Raw columns and clean names

Each row is one organisation in one month. The Period column looks like `MSitAE-JUNE-2025`.

| Raw column, as published | Clean name | Meaning |
|---|---|---|
| `Period` | `month_start` | Month of the data, parsed to the first day of the month. |
| `Org Code` | `org_code` | NHS organisation code, used as the key. The value `TOTAL` marks the published all-England row. |
| `Parent Org` | `region` | NHS England region. There are 7 values, with trailing spaces and the prefix NHS ENGLAND removed. |
| `Org name` | `org_name` | Organisation name in upper case. Four organisations changed name during the year. |
| `A&E attendances Type 1` | `t1_attendances` | Unplanned attendances at Type 1 departments, which are consultant-led 24-hour services with full resuscitation facilities. Booked appointments are excluded, as in definition A1i. |
| `A&E attendances Type 2` | `t2_attendances` | Unplanned attendances at Type 2 departments, which are consultant-led single specialty services such as ophthalmology or dental. Booked appointments are excluded, as in A1ii. |
| `A&E attendances Other A&E Department` | `oth_attendances` | Unplanned attendances at Type 3 departments and urgent treatment centres, excluding booked appointments, as in A1iii. Minor injury units, urgent care centres and walk-in centres that have not become urgent treatment centres still report as Type 3. Some of these services are run by providers that are not NHS trusts. |
| `A&E attendances Booked Appointments Type 1`, `Type 2` and `Other Department` | `t1_booked_attendances`, `t2_booked_attendances`, `oth_booked_attendances` | Booked appointments that were attended, for example booked through NHS 111 or a GP. Appointments that were not attended and planned follow-ups are excluded, as in A1iv to A1vi. NHS England's published headline figures reconcile only when these are included, but version 5.0 does not define a combined total, so the inclusion rests on that reconciliation. |
| `Attendances over 4hrs Type 1`, `Type 2` and `Other Department` | `t1_over_4hrs`, `t2_over_4hrs`, `oth_over_4hrs` | Patients whose total time in A&E, from arrival to admission, transfer or discharge, was 04:00:01 or longer, as in A2i to A2iii. These are paired with the unbooked attendance columns. |
| `Attendances over 4hrs Booked Appointments Type 1`, `Type 2` and `Other Department` | `t1_booked_over_4hrs`, `t2_booked_over_4hrs`, `oth_booked_over_4hrs` | The same count for booked appointments. Version 5.0 has no separate item for this. The pairing with booked attendances rests on internal consistency, because the over-four-hour count never exceeds attendances within either series, and on the reconciliation. |
| `Emergency admissions via A&E - Type 1`, `Type 2` and `Other A&E department` | `t1_emergency_admissions`, `t2_emergency_admissions`, `oth_emergency_admissions` | Emergency admissions, admission method 21, through that department type. They count patients who spent time in the department before being admitted as an emergency to the same provider, as in B1i to B1iii. |
| `Patients who have waited 4-12 hs from DTA to admission` | `dta_4_to_12h` | Patients whose wait from decision to admit, or from the end of A&E treatment if later, to admission was 04:00:01 to 12:00:00 inclusive, as in A3. Not split by department type. The wait of a transferred patient ends when they are collected. |
| `Patients who have waited 12+ hrs from DTA to admission` | `dta_12h_plus` | Patients whose same wait was 12:00:01 or longer, so strictly over 12 hours, as in A4. Not split by department type. This is not the same as total time in A&E. |
| `Other emergency admissions` | `other_emergency_admissions` | Emergency admissions that did not come through any A&E department of the same provider. Examples are direct admission by a GP, the bed bureau, an outpatient clinic or a mental health crisis team, transfers in of admitted patients from other hospitals, and home births, as in B1iv with admission methods 22 to 28 and 2A to 2D. Not used in the headline analysis. |

The prefix for Other A&E department in the clean names is `oth_` and not `other_`, so that it cannot collide with the organisation-level `other_emergency_admissions`. Using `other_` for both once produced a duplicate column, as described in decision 13 of [DECISIONS.md](DECISIONS.md).

## Database tables

The database is `data/processed/ae_2025_26.sqlite`.

| Table or view | Grain | Notes |
|---|---|---|
| `dim_month` | one row per month, 12 rows | label, days in month and source file |
| `dim_org` | one row per organisation code, 205 rows | latest name, display name, region, `has_type1` and `is_children_or_womens` |
| `fact_ae_type_month` | organisation, month and department type, 7,158 rows | attendances, over-four-hour counts, booked equivalents and emergency admissions, in long format |
| `fact_org_month` | organisation and month, 2,386 rows | measures that are not split by department type, which are the decision-to-admit waits and other emergency admissions |
| `published_totals` | one row per month, 12 rows | NHS England's own TOTAL rows, kept for reconciliation only |
| `v_ae_type_month` | organisation, month and department type | the facts joined to the dimensions, used by the dashboard and the analysis queries |

Rates such as four-hour performance and admission ratios are not stored. They are calculated from summed counts at the level each query needs.
