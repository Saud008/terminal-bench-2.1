# Plate closure ops workflow

This task is a **system-administration** host-local platclosectl plate-closure ops desk (hydrate → bind → seal). Operators admit offline TAN plate-solution scenario packs, bind spherical residuals into a staging matrix under WCS projection rules, and publish a digest-bound closure certificate only from a committed bind pass. Policy modules under /app/internal/ must keep lab journal rows, bind_pass counters, residual-matrix staging, and certificate republication aligned with the cited contracts.

Fixed ops order for every scenario:

1. `hydrate-plates` — journal the scenario load into `/app/state/plate-closure.db`
   (`lab_events` schema in lab-events-journal-schema.md)
2. `bind-residuals` — write the residual matrix and set `/app/state/bind-pass.json`
   to `{"bind_pass":1}` (or increment a positive bind_pass)
3. `seal-closure` — emit the certificate only when `bind_pass > 0`

`seal-closure` requires a prior successful `bind-residuals` (`bind_pass > 0`).
`bind-residuals` may succeed without a preceding `hydrate-plates` when the scenario
fixture is readable from the fixture root; hydrate is the journal step, not a hard
prerequisite for bind.

Reference math must match the cited WCS, projection, nudge, mask, and digest contracts in this docs set.

Pytest may invoke `/app/scripts/reset-state.sh` between cases to clear `/app/state`, `/app/work`, and `/app/output`.

The internal/decoy DSS plate label renderer is not on the plate-closure hot path.
