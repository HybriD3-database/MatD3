# MatD3 CHANGELOG

## v3.2.0 (November 2024)

- Added a function to filter results based on minimum and maximum band gap.
- Included dimensionality and stoichiometry in systems API results.
- Reformatted view of systems panel information.
- Fixed mapping of dimensionality for systems information.
- Removed dimensionality display for datasets.
- Removed dimensionality entry for datasets.

## v3.1.0 (October 2024)

- Implemented a feature to obtain reference information from .bib files.
- RIS reference parser now reads in more fields beyond the title.
- Stoichiometry representation supports formulas with parenthesis.

## v3.0.0 (September 2024)

- Implemented feature to display stoichiometries of materials (Thanks to Reyna Vrbensky!).

## v2.0.0 (September 2024)

- Updated code to support latest Python libraries (as of September 2024).
- Included feature to import reference information from RIS files (Thanks to Melosa Rao!).
- Solved SMTP email server error. Now users have to obtain a Google App password for `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`.
- Disabled email notifications for modifications to verified datasets.
