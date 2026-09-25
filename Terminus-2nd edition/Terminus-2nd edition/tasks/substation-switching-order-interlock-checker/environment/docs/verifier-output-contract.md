# Verifier output contract

Pytest invokes relayctl through /app/bin/relayctl and writes reports under /app/output/ using absolute paths including /app/output/verify-report.json, /app/output/sim-lockout.json, /app/output/sim-lockout2.json, /app/output/sim-order.json, /app/output/sim-energize.json, /app/output/sim-digest.json, /app/output/sim-ticket.json, /app/output/contract-parallel.json, /app/output/contract-ring.json, /app/output/contract-summary.json, /app/output/contract-reasons.json, /app/output/contract-buses.json, /app/output/hidden-lockout.json, /app/output/hidden-ring.json, /app/output/guard-decoy.json, /app/output/no-compile.json, and /app/output/bad-seed.json.

Bundled scenario fixtures include /app/fixtures/scenarios/basic-isolation.json, /app/fixtures/scenarios/dual-source-ring.json, /app/fixtures/scenarios/lockout-blocks-close.json, /app/fixtures/scenarios/step-order-trap.json, /app/fixtures/scenarios/energize-propagation.json, and /app/fixtures/scenarios/parallel-path.json. scenario_id values mirror the basename without .json.

Hidden overlay scenarios include tb3-lockout-bypass and tb3-energize-ring under /opt/verifier-fixtures/sublock/scenarios/ with files tb3-lockout-bypass.json and tb3-energize-ring.json.

Independent step contract math for pytest lives at /app/scripts/interlock_contract/step_contract.py. Import the module as step_contract when comparing verify-order JSON to contract math.

Fixture paths include /app/fixtures/seeds.json, /app/var/sub/yard.snapshot, and /app/var/sub/loto.ticket. Example energized bus identifiers include bus-src and bus-s2. Seed mismatch probes use wrong-seed as a negative control.
