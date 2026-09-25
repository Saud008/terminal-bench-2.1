Software RAID arrays under mdadm can be reshaped while online, but a grow that fires with an armed write-intent bitmap, a held spare, or an illegal level hop can leave the host degraded mid-window. mdreshape must run on the working Bash tree under /app and produce reshape eligibility for each array plus a digests-backed atlas before any grow is scheduled.

Required CLI at /app/bin/mdreshape:
  mdreshape scan --scenario <name> --run-id <id>
  mdreshape compile --run-id <id>
  mdreshape publish --run-id <id> --output <path>

scan writes /app/state/inventory.json and /app/state/run-meta.json. compile writes /app/state/reshape-ledger.json. publish writes /app/output/mdreshape_eligibility_atlas.json (or --output). Eligible rows use a deterministic rank invariant. Salted array names follow the truncated salt digest rules in array-fleet-schema.md.

Normative contracts:
- /app/docs/engineering-problem-contract.md — RAID geometry failure envelope
- /app/docs/mdreshape-cli.md — flags and load alias
- /app/docs/array-fleet-schema.md — host_salt and load_seq
- /app/docs/write-intent-bitmap-rules.md
- /app/docs/spare-slot-hold-rules.md
- /app/docs/active-disk-floor-rules.md
- /app/docs/raid-level-transition-rules.md
- /app/docs/reshape-hour-budget-rules.md
- /app/docs/eligibility-rank-rules.md
- /app/docs/reshape-ledger-shape.md
- /app/docs/eligibility-atlas-seal.md
- /app/docs/maintenance-window-ops.md
- /app/docs/scenario-matrix.md
- /app/docs/reshape-eligibility-rationale.md

Public fixtures: /app/fixtures/scenarios (for example basic-reshape). Hidden trees: /opt/verifier-fixtures/mdreshape via TB3_SCENARIO_DIR. Reset with /app/scripts/reset-state.sh. Independent math lives in tests/mdreshape_mathlib.py (not imported by /app). Subprocess helpers live in tests/mdreshape_harness.py. Salt helpers under /app/internal/raidops/scanstage/salt_hash.py use hashlib. The decoy /app/internal/raidops/decoy/slot_name_lex_helper.sh is unused.

Do not modify /app/docs/, /app/config/, or /app/fixtures/.
