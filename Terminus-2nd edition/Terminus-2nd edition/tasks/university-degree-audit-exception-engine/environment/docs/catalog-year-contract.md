# Catalog year contract

Each scenario_meta row stores catalog_year as the student locked curriculum year. Course eligibility uses catalog_year_introduced on courses rows: a course counts only when catalog_year_introduced is less than or equal to the student locked catalog_year.

Never derive the active catalog year from transcript enrollment terms or from the maximum catalog_year_introduced among enrolled courses. The locked catalog_year column in scenario_meta is authoritative for catalog precedence.

Audit calendar date from scenario_meta or TB3_AUDIT_DATE does not replace catalog_year for course eligibility filtering.
