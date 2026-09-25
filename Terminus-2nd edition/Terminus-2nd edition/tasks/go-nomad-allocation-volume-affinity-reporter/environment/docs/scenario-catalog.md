# Scenario catalog

Bundled scenarios under /app/fixtures/scenarios/:

- /app/fixtures/scenarios/basic-volume-join.json: CSI mountlink join to a single EBS volume
- /app/fixtures/scenarios/node-class-precedence.json: hard node.class filter with affinity ranking across pools
- /app/fixtures/scenarios/reschedule-attempt-chain.json: failed reschedule attempt totals across replacements
- /app/fixtures/scenarios/stale-allocation-filter.json: superseded rows, drain stop desired status, and modify_index stale suppression
- /app/fixtures/scenarios/affinity-soft-rank.json: spread-adjusted affinity ordering after constraint pass

Hidden overlays under /opt/verifier-fixtures/scenarios/ follow the same contracts with namespace salt and modify_index stale edge cases.
