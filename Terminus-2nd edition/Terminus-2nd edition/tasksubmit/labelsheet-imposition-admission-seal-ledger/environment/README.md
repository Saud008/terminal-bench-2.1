# sheetd labelsheet imposition admission control plane

Host-local sheetd admits label catalog impose sets, applies gutter-edge / sample-window / press-rotate / lot-scale gates, and seals imposed sheet PNG plus checksum ledger exports. Ops contracts live under `/app/docs/`.

```bash
sheetd impose --catalog /app/fixtures/catalog.json --marks /app/fixtures/marks \
  --set core-marks --seed 7 --sheet-out /app/output/sheet.png --ledger-out /app/output/ledger.json

sheetd sample --sheet /app/output/sheet.png --ledger /app/output/ledger.json \
  --mark arrow --frame 0 --u 0.0 --v 0.0
```

CLI path: `/app/bin/sheetd` after `bash /app/scripts/rebuild-sheet.sh` from `/app`.
