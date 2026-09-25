# Engineering problem contract

Port container demurrage clock ledger computes carrier invoices from gate events, free time, holds, closures, and tiered tariffs.

## Problem shape

Operators load yard scenarios, stage dwell clocks with pause and exclusion rules, then publish JSON invoices. The engineering task is yard billing pipeline correctness across SQLite state, ledger JSON, and invoice JSON.

## Independent verification

Pytest reference math in /tests/demur_refmath.py recomputes eligible days, tier buckets, and invoice totals without reading Go sources.

## Anti-hardcoding

DEMUR_SEED remaps container identifiers on load when set. TB3_FIXTURE_DIR redirects fixture roots to /opt/verifier-fixtures/demurctl for hidden scenarios.

## Module boundaries

yardkernel validates scenario shape. yardsql owns persistence. yardbundle sorts gate events. holdpolicy, pauseclock, closurecal, and tarifftier own dwell math layers.
