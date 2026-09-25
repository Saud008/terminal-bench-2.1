Labelsheet imposition administrators run the host-local sheetd labelsheet imposition admission control plane at /app/bin/sheetd. Each offline ops pass admits label catalog JSON and mark roster PNGs from /app/fixtures/, enforces gutter, normalized sample-window, press-rotate, lot-scale, and oversized admission gates, stages sheet imposition state, then publishes sealed imposed sheet PNG and checksum ledger exports only after those gates pass. There is no remote print fleet. This is a system-administration host-local labelsheet imposition ops control plane; keep catalog admission, gutter-edge gates, sealed-sheet sample audits, and sealed export aligned. It is not a generic service repair exercise.

Normative contracts: /app/docs/sheet-ops-workflow.md for the control-plane overview, /app/docs/sheet-contract.md for gutter sample-window press-rotate and size gates, /app/docs/ledger-schema.md for sealed ledger fields and checksum policy, /app/docs/exit-codes.md for impose and sample exit obligations, and /app/docs/sheet-runtime-paths.md for fixture and output paths.

sheetd impose --catalog PATH --marks PATH --set NAME --seed N --sheet-out PATH --ledger-out PATH must admit one catalog set, apply gutter press-rotate and lot-scale gates, and publish sealed sheet PNG plus ledger JSON at the caller-provided output paths only when admission succeeds.

sheetd sample --sheet PATH --ledger PATH --mark ID --frame N --u U --v V must audit a sealed sheet cell at normalized sample-window coordinates for one mark frame and exit per /app/docs/exit-codes.md.

Example ops passes:

sheetd impose --catalog /app/fixtures/catalog.json --marks /app/fixtures/marks --set core-marks --seed 7 --sheet-out /app/output/sheet.png --ledger-out /app/output/ledger.json

sheetd sample --sheet /app/output/sheet.png --ledger /app/output/ledger.json --mark arrow --frame 0 --u 0.0 --v 0.0

Optional environment overlays for verifier fixtures may set TB3_VERIFIER_FIXTURES when tests document it. The control plane is rebuilt from /app sources before checks. Keep /app/bin/sheetd on PATH. Admission libraries live under /app/lib/sheet/; the decoy helper stays outside the impose admission path.
