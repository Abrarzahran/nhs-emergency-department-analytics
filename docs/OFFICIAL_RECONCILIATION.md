# Reconciliation with NHS England's published figures

The figures below come from extracts of NHS England's monthly Statistical Commentary PDFs, obtained through a web search tool. They are secondary extractions and have not been checked against the PDFs themselves. The links are listed at the end so that the values can be confirmed. Exact agreement across many independent numbers makes a transcription error unlikely, but it does not replace reading the source.

## Result: the published headline includes booked appointment attendances

| Month | Published Type 1 % within 4 hours | This project, booked included | This project, booked excluded | Published all-department % | This project, booked included |
|---|---|---|---|---|---|
| Apr 2025 | 60.2 | 60.2 | 59.8 | Not available | 74.8 |
| Sep 2025 | 61.1 | 61.1 | 60.8 | 75.1 | 75.1 |
| Oct 2025 | 60.1 | 60.1 | 59.9 | 74.1 | 74.2, see below |
| Nov 2025 | 60.3 | 60.3 | 60.1 | 74.2 | 74.2 |
| Dec 2025 | 59.6 | 59.6 | 59.3 | 73.8 | 73.8 |
| Jan 2026 | 57.3 | 57.3 | 57.0 | 72.5 | 72.5 |
| Feb 2026 | 59.4 | 59.4 | 59.1 | 74.1 | 74.1 |
| Mar 2026 | 64.1 | 64.1 | 63.9 | 77.1 | 77.1 |

- Including booked attendances reproduces the published Type 1 figure in 8 of 8 months. Excluding them misses in 8 of 8.
- Other published figures also agree with the supplied files:
  - In December 2025, 27.7% of Type 1 attendances resulted in admission. This holds only when booked attendances are in the denominator, and the figure is 28.3% otherwise.
  - In January 2026, 71,517 patients were delayed over 12 hours from decision to admit.
  - In January 2026, 161,141 patients were delayed over 4 hours from decision to admit. This equals the 4 to 12 hour count plus the over 12 hour count, so the two bands do not overlap.
  - In October 2025 there were 83,524 booked attendances.
  - There were 121 reporting trusts with Type 1 departments, and the data have 121.
- The commentaries state that booked appointments have been counted within attendance figures since August 2020, and they report a separate series that excludes booked attendances. This is consistent with the headline including them.

The project originally excluded booked attendances by default, as an assumption. The comparison above showed that this was not the published basis. The default, the SQL queries, the findings and the documentation now include them, and the unbooked-only view remains as an option. The reconciliation tests were added afterwards to record the result.

## Remaining differences

These are not adjusted.

| Item | Published | Supplied files | Note |
|---|---|---|---|
| Oct 2025 all-department % within 4 hours | 74.1, with 1,777,827 within 4 hours | 74.19, with 1,781,392 within 4 hours, which is 3,565 more or 0.2% | October 2025 was reported as a revised file, see [REVISIONS.md](REVISIONS.md). This is consistent with the difference but does not prove it. |
| Dec 2025 over-12-hour decision-to-admit waits | 50,775 | 50,789 | December 2025 was also reported as revised, and the same caveat applies. The difference is +14. Total attendances differ by -876. |
| Mar 2026 booked attendances | 80,936 | 80,925 | March 2026 was also reported as revised, and the same caveat applies. The difference is -11. Total attendances differ by +19. |

Figures in this project can therefore differ slightly from the original commentaries in the revised months. The full comparison is in [REVISIONS.md](REVISIONS.md).

## Definitions

| Item | Status |
|---|---|
| The four-hour measure is the share of patients admitted, transferred or discharged within 4 hours of arrival, against a 95% standard | Stated in the commentaries, from extracts. |
| The headline percentage includes booked attendances | Supported by the commentary wording and by the numerical agreement above. |
| Type 1 performance is reported separately from all-department performance and from Type 3 | Stated in the commentaries. Other A&E department as Type 3 or urgent treatment centre is confirmed by definition A1iii in version 5.0. |
| The 12-hour measure here runs from decision to admit to admission | Confirmed by the exact match with the commentary's wording on patients delayed more than 12 hours from decision to admit to admission. It is not the separate arrival-based measure of 12 hours in a department, which NHS England publishes from ECDS data in a different release. This project does not use that measure. |
| Band boundaries | Confirmed by definitions A3 and A4 in version 5.0. The 4 to 12 hour band is 04:00:01 to 12:00:00 inclusive and over 12 hours is 12:00:01 or longer. |
| What other emergency admissions contains | Confirmed by definition B1iv in version 5.0. These are emergency admissions not made through any A&E department of the same provider. |
| Column definitions | Version 5.0 of August 2020 was read in full, as set out in [DEFINITIONS_CROSSWALK.md](DEFINITIONS_CROSSWALK.md). It does not define the headline percentage or the booked over-four-hour columns, so the booked-inclusive basis rests on the reconciliation. |

## Confirming the figures

The release page is https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2025-26/ and it links to the definitions and notes.

The values in `tests/test_official_reconciliation.py` can be checked against these commentaries. They cover the Type 1 percentage, the all-department percentage, the 27.7% admission figure in December, 71,517 and 161,141 in January, and 83,524 in October.

- March 2026: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/04/Statistical-commentary-March-2026-G4dal2.pdf
- April 2026, which gives the April 2025 Type 1 figure of 60.2%: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/05/Statistical-commentary-April-2026-G4dal2.pdf
- January 2026: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Statistical-commentary-January-2026-tSD37a.pdf
- December 2025: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/01/Statistical-commentary-December-2025-Rd3l0d.pdf
- October 2025: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/11/Statistical-commentary-October-2025-5grfp.pdf

The February 2026, November 2025 and September 2025 values come from the prior-month comparisons in the March 2026, December 2025 and October 2025 commentaries.

Two points are still open. One is the wording on booked appointments and on the Type 3 mapping in the commentaries themselves. The other is whether the CSV files on the release page are the revised versions that were used here, and whether that explains the three small differences above.
