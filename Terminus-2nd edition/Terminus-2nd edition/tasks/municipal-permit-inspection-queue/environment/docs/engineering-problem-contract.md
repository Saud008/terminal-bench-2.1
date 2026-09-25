# Engineering problem contract — municipal-permit-inspection-queue

Task identity 751ee9c95c — municipal permit inspection roster with compliance graph compile.

## Core engineering concept

Compile a weekly inspection manifest from permit bundles through a compliance policy graph, moratorium hold mask, calendar eligibility filter, violation-weighted score ledger, and inspector binding. Unlike single-pass roster compilers, mpiqctl materializes an intermediate policy graph and hold mask before sequencing. SQLite batch source rows feed staged work artifacts; the digest-sealed manifest is the publish sink. Policy graph closure and constraint propagation across lane edges are documented in /app/docs/policy-graph-contract.md.

## Compliance graph compile ladder

| Phase | Artifact | Role |
|-------|----------|------|
| snapshot-load | /app/state/permit.db | SQLite permit, inspector, violation rows |
| compile-policy | /app/work/policy-graph.json + /app/intermediate/compliance-trace.json | Lane edges and policy traverse trace |
| apply-holds | /app/work/hold-mask.json | District moratorium dominance mask |
| filter-blackouts | /app/work/eligible-dates.json | Calendar eligibility per permit |
| score-queue | /app/work/violation-ranks.json | Composite violation score ledger |
| bind-inspectors | queue_entries table | Cert-floor inspector binding |
| publish-queue | /app/output/permit-queue-manifest.json | Digest-sealed manifest publish |

## Root cause envelope

Cert floor off-by-one, moratorium min hold instead of max hold, blackout end-day treated as blocked, recency decay inverted, electrical lane mis-route, publish gate reading publish_pass instead of queue_pass, or score stage skipping calendar eligibility.

## Verifier constraint

Bundled scenarios must match independent reference math for queue_entries and queue_digest. TB3_FIXTURE_DIR selects hidden moratorium bias and blackout end-day traps under /opt/verifier-fixtures/mpiqctl.
