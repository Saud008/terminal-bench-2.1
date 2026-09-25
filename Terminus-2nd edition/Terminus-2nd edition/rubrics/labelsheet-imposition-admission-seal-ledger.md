# Platform rubric — labelsheet-imposition-admission-seal-ledger

**Task folder:** tasks/labelsheet-imposition-admission-seal-ledger/
**Written:** 2026-07-19T20:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent aligns catalog, impose, sample-window, ledger, and compose modules so admission and sealed export match the ops contracts, +3
Agent applies gutter_px seed policy and replicates edge-pixel fill into the gutter, not transparent fill, +3
Agent emits inner-content normalized sample windows that exclude the gutter for edge samples, +3
Agent places press-rotated marks with swapped shelf size and ninety-degree clockwise compositing, +2
Agent keeps multi-frame marks and lot-scale seed multipliers consistent across impose sets, +2
Agent aborts oversized scaled marks with exit code 2 before writing sealed outputs, +2
Agent rebuilds sheetd from /app sources before verifier runs, +1
Agent leaves /app/docs and /app/fixtures unchanged, +1
Agent fixes only sample-window math while gutter fill or press-rotate shelves stay wrong, -3
Agent fills gutter with transparent pixels instead of edge replication, -3
Agent edits protected fixtures or the verifier reference under /tests to force a pass, -5
