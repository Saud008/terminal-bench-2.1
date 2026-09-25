# Sheet ops workflow

Host-local labelsheet imposition admission control plane (`sheetd`).

## Ops pass order

1. Admit label catalog JSON and mark roster files for one impose set and seed.
2. Apply gutter, edge replication into the gutter, press-rotate shelf, lot-scale, and oversized admission gates.
3. Stage imposed layout in memory (no remote print fleet publish).
4. Seal PNG sheet and checksum ledger exports only after gates pass.
5. Optional sample audits sealed sheet cells for one mark frame.

## Normative contracts

- `/app/docs/sheet-contract.md` — gutter-edge, sample-window, press-rotate, duplicate frames, lot-scale, size limit
- `/app/docs/ledger-schema.md` — sealed ledger fields and checksum
- `/app/docs/exit-codes.md` — impose and sample exit codes
- `/app/docs/sheet-runtime-paths.md` — fixtures, outputs, rebuild path
