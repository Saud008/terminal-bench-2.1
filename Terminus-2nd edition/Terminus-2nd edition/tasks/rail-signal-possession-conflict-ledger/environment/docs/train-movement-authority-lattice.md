# Train movement authority lattice

Movement claims carry implicit authority ranks used only for emit metadata, not for suppression.

| Claim kind | Authority label | Notes |
|------------|-----------------|-------|
| maintenance possession | maintainer | track access for engineering |
| train reservation | dispatcher | scheduled movement |
| crisis override | crisis | priority 0 suppresses other authorities in its zone |

When multiple conflict reasons apply to the same participant pair, reasons array lists all tokens sorted ascending. possession_overlap and possession_train are distinct tokens.

Emit block lists within a conflict row sort by ascending kilometer from the scenario block table, then block_id lexicographically when kilometers tie.
