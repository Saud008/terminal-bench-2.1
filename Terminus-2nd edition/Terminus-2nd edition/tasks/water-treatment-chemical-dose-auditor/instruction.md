Municipal water treatment operators must implement wtcdctl on the working Rust baseline under /app. wtcdctl performs numerical simulation of plant mass allocation with unit-aware calibration, probe-turbidity correlation, and limit-breach closure from live probes, batch concentrations, turbidity probes, operator elevation requests, and window eligibility. Results stage a shift-vault artifact keyed by a revision token, then publish a breach summary from that vault alone.

Install wtcdctl at /app/bin/wtcdctl from /app/target/release/wtcdctl with exactly two subcommands:

  wtcdctl load-shift-dose --plant <plant-id> --shift <name>
  wtcdctl export-breach-atlas --plant <plant-id> --output <path>

wtcdctl load-shift-dose loads the named plant shift bundle, converts batch concentration values to milligrams per liter, scales probe readings to liters per minute, skips minutes failing the window rule, applies probe-weighted allocation with turbidity uplift and per-minute ceiling caps, validates operator elevation authorization, forward-fills probe gap spans, and writes a shift-vault JSON at /app/work/dose-ledger/<plant-id>.json. ledger_revision_token derivation and vault field names appear in /app/docs/shift-store-contract.md.

wtcdctl export-breach-atlas reads only the shift vault for the plant id and writes a breach summary JSON to the caller-provided --output path. Breach severity rank ladder, summary counters, and breach_atlas_seal rules appear in /app/docs/limit-breach-contract.md.

Batch token composition follows /app/docs/lot-token-contract.md. Concentration scaling follows /app/docs/unit-scale-contract.md. Probe scaling follows /app/docs/rate-scale-contract.md. Window eligibility follows /app/docs/dwell-window-contract.md. Per-minute ceiling caps follow /app/docs/minute-ceiling-contract.md. Probe-weighted allocation and turbidity uplift follow /app/docs/mass-blend-kernel.md. Calibration closure and unit correlation rules appear in /app/docs/calibration-closure-contract.md. Operator elevation authorization follows /app/docs/role-elevation-policy.md. Probe gap forward-fill limits follow /app/docs/gap-forward-policy.md. The plant audit workflow and vault-only summary boundary appear in /app/docs/plant-audit-workflow.md.

Shift bundles and plant ids live under /app/fixtures/plant_shifts/. Verifier pytest may write breach summary samples under /app/output/. The bundled inventory and behaviors each shift exercises appear in /app/docs/shift-bundle-catalog.md. Runtime-supplied shift overlays follow those same contracts.

Compile wtcdctl with /usr/local/cargo/bin/cargo build --release from /app. Independent verifier contract math lives in /app/scripts/wtcda_refmath.py. Pytest helpers for subprocess CLI invocation live in /app/scripts/wtcda_subprocess.py. Run /app/scripts/reset-workspace.sh before cross-run verifier cases. The decoy turbidity chart module is not used by load-shift-dose or export-breach-atlas.
