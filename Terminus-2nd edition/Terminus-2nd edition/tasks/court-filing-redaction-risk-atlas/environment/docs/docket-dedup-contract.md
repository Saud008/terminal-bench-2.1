# Docket deduplication

When multiple docket rows share a matter, prefer primary_flag=true over latest filed_at filed_clock.

PickPrimaryDocket returns the primary docket number when any row has primary_flag=true.

Bundled scenario docket-primary-select uses primary number CV-2024-005 over a newer non-primary duplicate row.
