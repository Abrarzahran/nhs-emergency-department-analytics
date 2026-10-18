# Data provenance and licence

| | |
|---|---|
| Publisher | NHS England |
| Release | A&E Attendances and Emergency Admissions 2025-26, monthly provider-level CSV files for April 2025 to March 2026 |
| Page | <https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2025-26/> |
| Files | `raw/` holds 12 unmodified CSV files. SHA-256 checksums are in `MANIFEST.csv`. |
| Content | Organisation-level monthly aggregate counts. There is no patient-level data. |
| Revisions | Some monthly files have been revised by NHS England. See [`../docs/REVISIONS.md`](../docs/REVISIONS.md). |

## Licence and attribution

These files are copyright NHS England. They are not covered by this repository's MIT licence, which applies to the original code and documentation only. See [`../NOTICE.md`](../NOTICE.md).

> Source: NHS England, *A&E Attendances and Emergency Admissions 2025-26*,
> <https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2025-26/>.
> Contains public sector information licensed under the Open Government Licence v3.0,
> <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>.

### Verification status

| Point | Status |
|---|---|
| NHS England's terms and conditions say website information may be re-used under the Open Government Licence, excluding logos, photographs and content identified as another party's copyright. The page is <https://www.england.nhs.uk/terms-and-conditions-2/>. | Confirmed by the project author reading that page. The wording is also consistent with a search extract of the same page. |
| The CSV files contain no licence, copyright or restriction text. | Verified by searching all 12 files, which hold headers and data only. |
| The NHS England definitions document, version 5.0, contains no licence statement. | Verified by reading it in full. It neither grants nor restricts anything. |
| The 2025-26 release page imposes no additional restriction on the CSV files. | Not checked, because the page could not be opened during the build. This is a low residual risk, and the page footer and notes can be checked before publication. |
| The version of the Open Government Licence named on the terms page. | Not confirmed. Version 3.0, the current version, is cited. |
| The files contain no third-party copyright content. | Consistent with the files, which hold organisation-level counts only. Not separately verifiable. |

## Refreshing the data

Download the monthly CSV files from the release page into `raw/`. No other CSV file may be placed there. Then run `python scripts/build_database.py`. The build stops if a header changes or a validation check fails.
