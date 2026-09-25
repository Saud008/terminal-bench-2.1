Labelsheet imposition playtest

Build the labelsheet imposition playtest, an offline warehouse label-lot playfield planner for catalog admission, gutter-edge traps, press-rotate shelves, lot-scale gates, and sealed sheet-ledger win conditions on the working baseline under `/app`. The planner loads label catalog and mark roster packs from `/app/fixtures/`, applies gutter sample-window and oversized admission scoring, audits sealed-sheet sample cells, then seals imposed sheet PNG and checksum ledger exports when the sheet-ledger win condition is met. This is a games labelsheet-imposition playtest and sealed-ledger workflow: keep catalog admission, gutter-edge gates, press-rotate shelves, lot-scale multipliers, staging-before-export, sealed-sheet sample audits, and checksum ledger exports aligned. It is not a generic software-engineering module rebuild, PNG compositor debugging exercise, pytest harness, CI tooling, or service-repair workflow.

sheetd is available at `/app/bin/sheetd`. Normative playtest contracts live under `/app/docs/`: sheet-ops-workflow.md, sheet-contract.md, ledger-schema.md, exit-codes.md, and sheet-runtime-paths.md.

sheetd impose --catalog PATH --marks PATH --set NAME --seed N --sheet-out PATH --ledger-out PATH must admit one catalog set, apply gutter press-rotate and lot-scale gates, and publish sealed sheet PNG plus ledger JSON at the caller-provided output paths only when admission succeeds.

sheetd sample --sheet PATH --ledger PATH --mark ID --frame N --u U --v V must audit a sealed sheet cell at normalized sample-window coordinates for one mark frame and exit per /app/docs/exit-codes.md.

Example playtest passes:

sheetd impose --catalog /app/fixtures/catalog.json --marks /app/fixtures/marks --set core-marks --seed 7 --sheet-out /app/output/sheet.png --ledger-out /app/output/ledger.json

sheetd sample --sheet /app/output/sheet.png --ledger /app/output/ledger.json --mark arrow --frame 0 --u 0.0 --v 0.0

Optional environment overlays for verifier fixtures may set TB3_VERIFIER_FIXTURES when tests document it. Keep /app/bin/sheetd on PATH. The decoy helper stays outside the impose admission path.
