# Crosswalk between the NHS England definitions and this project

Source document: NHS England and NHS Improvement, A&E Attendances and Emergency Admissions Monthly Return Definitions, version 5.0, final, August 2020. All 16 pages were read for this comparison. References such as A1i, A3, B1iv and FAQ 8 are to sections of that document.

Status labels used below:

- Confirmed: the document states it.
- Corrected: the project was changed after the document was read.
- Not established: the document does not settle it, so the point is left open.
- Caveat: a limitation that is now stated in the dashboard or the documentation.

## 1. Department types

| Item | What the document says | In this project | Status |
|---|---|---|---|
| Type 1 | A consultant-led 24-hour service with full resuscitation facilities and designated accommodation for accident and emergency patients. It is increasingly called an Emergency Department. | Described as a major emergency department. | Confirmed, wording tightened |
| Type 2 | A consultant-led single specialty accident and emergency service, with ophthalmology and dental as examples. | Described as single specialty. The only Type 2 providers in the data are Moorfields, which is an eye hospital, and Liverpool Women's. | Confirmed |
| Other A&E department | Definitions A1iii, A1vi, A2iii and B1iii define Other A&E department as Type 3 departments and urgent treatment centres. Minor injury units, urgent care centres and walk-in centres that are not urgent treatment centres continue to report as Type 3. FAQ 1 also covers independent sector services commissioned by clinical commissioning groups, and FAQ 8 lets an acute trust report a nearby Type 3 service that it runs. | Described as Type 3, urgent treatment centres and similar services. | Confirmed. This was an assumption before the document was read. |
| Reporting threshold | A department is classified as a type only if it averages over 200 attendances a month, calculated over a quarter. | A warning check counts the series that average 200 or fewer a month over the 12 months. There are 11 of 338 active series, including Okehampton Medical Centre and Enderby Leisure Centre. They are kept as published. | Confirmed, new check added |
| Provider codes | NHS trusts report against the 3-character provider code, and other organisation types use other codes. | A check confirms that all 121 Type 1 providers have 3-character codes. The 35 five-character and 13 six-character codes belong to other providers. | Confirmed, new check added |

## 2. Attendances, booked appointments and four-hour performance

| Item | What the document says | In this project | Status |
|---|---|---|---|
| Attendance | Unplanned attendances, with attendance category 1 to 3. Planned follow-ups and telephone or video consultations are excluded. Definitions A1i to A1iii say to exclude booked appointments. | The attendance columns are treated as unbooked, unplanned attendances. | Confirmed, dictionary wording corrected |
| Booked appointments | Definitions A1iv to A1vi cover booked appointments that are attended, for example through NHS 111, NHS 111 First, a GP booking at an urgent treatment centre, or Covid-19 arrangements. Appointments not attended and planned follow-ups are excluded. The clock for a booked appointment starts at the appointment time, or at arrival if the patient is late. | The booked columns are kept as a separate series. | Confirmed |
| Four-hour breach | Definitions A2i to A2iii count total time in A&E from arrival to admission, transfer or discharge. A patient is counted at 04:00:01 or longer, and not counted at 04:00:00 or less. | A wait within four hours means 4 hours or less, and a breach means 04:00:01 or more. | Confirmed |
| Over-four-hour items for booked appointments | The document has none. Items A2i to A2iii are the only over-four-hour items, and a note says patients who spend time in A&E should be reported under them if appropriate. | The supplied CSV files have separate over-four-hour columns for booked appointments, so they follow a later layout than version 5.0. The project pairs those columns with booked attendances. | Not established. The pairing is supported by internal consistency, with no case of an over-four-hour count above attendances in either series, and by the reconciliation with published figures. |
| Percentage within four hours | Not defined anywhere in the document. It defines counts only, with no percentage and no total that combines booked and unbooked attendances. | The percentage is one minus the over-four-hour count divided by attendances, using summed counts that include booked appointments in both the numerator and the denominator. | Not established by the document. The basis is the match with NHS England's published monthly figures, in [OFFICIAL_RECONCILIATION.md](OFFICIAL_RECONCILIATION.md). That is evidence, not a definition. |
| Percentage of Type 1 attendances resulting in admission | Not defined in the document. | Type 1 admissions divided by Type 1 attendances plus Type 1 booked attendances. This matches one published figure. | Not established. Caveat: the admissions in a month and the attendances in the same month are not the same group of patients, and the streaming and same-day emergency care rules below change what is counted. |

## 3. Waits from decision to admit

| Item | What the document says | In this project | Status |
|---|---|---|---|
| Definition A3, 4 to 12 hours | Patients whose wait from decision to admit to admission is 04:00:01 to 12:00:00 inclusive. | `dta_4_to_12h`, labelled 4 to 12 hours, up to 12:00:00. | Confirmed, boundary now stated |
| Definition A4, over 12 hours | Patients whose wait is 12:00:01 or longer. | `dta_12h_plus`, labelled over 12 hours in the dashboard, README and SQL. | Confirmed, label corrected from 12 plus |
| What is measured | The wait runs from the decision to admit, or the end of A&E treatment if that is later, to admission. Admission means leaving to a ward, a theatre, a diagnostic test on the way to a bed, or a same-day emergency care unit. FAQ 4 states that this is not the same as total time in A&E. | The dashboard caption states the rule, including the end of treatment condition. | Confirmed, caption corrected |
| Transfers | The wait of a transferred patient ends when the ambulance crew collects them, as in FAQ 6. | A caption states this. | Caveat |
| Split by department type | A3 and A4 are single counts of emergency admissions via A&E, with no split by type. | Held at organisation level and not by type. | Confirmed |
| Waits per admission ratio | Not defined. A3 and A4 include patients transferred to another provider, while B1i to B1iii count only patients admitted to the same provider, so the two counts cover different groups. | An earlier version showed 12-hour waits per 1,000 emergency admissions in SQL query 7. That column was removed, and the query now ranks counts only. | Corrected |

## 4. Emergency admissions

| Item | What the document says | In this project | Status |
|---|---|---|---|
| Admissions via A&E, B1i to B1iii | Emergency admissions via Type 1, Type 2 or Type 3 departments, with admission method 21. They count patients who spent time in that department before being admitted as an emergency to the same provider. | Matches the `emergency_admissions` values by type. The captions mention the same provider condition. | Confirmed, caveat added |
| Other emergency admissions, B1iv | All emergency admissions not made through an A&E department of the same provider, for example admission directly by a GP. The admission methods are 22 via a GP, 23 via the bed bureau, 24 via a consultant outpatient clinic, 25 via a mental health crisis resolution team, 28 other means, 2A an A&E department of another provider where the patient had not been admitted, 2B an emergency transfer of an admitted patient from another hospital, 2C a baby born at home as intended, and 2D other emergency admission. | This was assumed to mean admissions not via A&E and is now confirmed. It is not used in any headline figure or ranking, because it includes transfers in and direct admissions that are unrelated to A&E performance. | Confirmed, description expanded |
| Who reports admissions | All providers that admit at least 40 emergency patients a month, including those with no A&E department. | This explains the 9 providers that report admissions but no A&E attendances in SQL query 9. | Confirmed |

## 5. Rules that affect comparisons between trusts

- Streaming, in examples A to D of the document: a patient streamed from Type 1 to a co-located Type 3 service is counted as a single Type 3 attendance, including any breach. A patient streamed to same-day emergency care on arrival is not an A&E attendance at all. A patient treated first and then moved to same-day emergency care is a Type 1 attendance. Trusts with different streaming arrangements therefore have different Type 1 populations, and Type 1 percentages and admission ratios are not fully like for like. The data do not allow this to be measured or adjusted for.
- Admission to a same-day emergency care unit counts as admission for the clock, as in A2, which can affect admission counts.
- Attendances are recorded in the period in which they end, including across month ends.
- Early pregnancy units, genitourinary medicine and sexual health clinics, and emergency inpatient clinics are not counted as A&E attendances.

## 6. Open points

| Item | Position |
|---|---|
| Data licence | The definitions document has no licence statement. The licensing basis is NHS England's terms and conditions, which allow re-use of website information under the Open Government Licence, as set out in [../NOTICE.md](../NOTICE.md) and [../data/README.md](../data/README.md). Any separate restriction on the CSV files stated on the release page has not been confirmed. |
| Formula for the headline percentage and the inclusion of booked appointments | Not in version 5.0. The project keeps the booked-inclusive calculation because it reproduces NHS England's published Type 1 figure in all 8 months checked, and states that the document does not itself establish it. |
| Definition of the separate booked over-four-hour columns | Not in version 5.0, which predates them. |
| Whether a newer definitions version exists | The NHS England A&E statistics page was reported to list version 5.0 as the current definitions. That page has not been re-checked as part of this documentation. |
| Which files were revised, and whether the revisions explain the small differences | The release page was reported to list October 2025, December 2025 and March 2026 among the revised files. Those are the only months with differences. The dates are not recorded and the cause is not proven. See [REVISIONS.md](REVISIONS.md). |
| Whether the PDF used here is identical to the version at the NHS England link | Not confirmed. This comparison used a downloaded copy of version 5.0. |
| Accuracy of the commentary figures in the reconciliation | The published figures were obtained from extracts of the commentary PDFs and have not been checked against the PDFs themselves. |
| NHS England's data quality guidance page | Not reviewed. NHS England's commentaries say that submissions are checked against previous submissions and that unusual variation is followed up. This comes from extracts and has not been confirmed. |
