The ConnMan-style roam helper at /app/scripts/connman-roamctl simulates WiFi handoff from scenario fixtures under /app/fixtures/scenarios/, but exports disagree with the contract docs under /app/docs/. Repair the Bash modules under /app/lib/roam/ so connman-roamctl simulate matches the referenced schemas for every scenario id in /app/fixtures/catalog.json and every seed in /app/fixtures/seeds.json, including hidden verifier scenarios when TB3_SCENARIOS_DIR points at an absolute directory.

Roam finite-state transitions, scan ledger credits, service preference ranking, DHCP renew gateway selection, and hidden-network consent gating must follow /app/docs/fsm-states.md, /app/docs/scan-ledger-format.md, /app/docs/service-ranking.md, /app/docs/dhcp-renew.md, and /app/docs/handoff-report-schema.md. Scenario field definitions are in /app/docs/scenario-format.md.

The environment is offline. Change only Bash under /app/lib/roam/. Do not edit /app/docs/, /app/fixtures/, or /tests/.
