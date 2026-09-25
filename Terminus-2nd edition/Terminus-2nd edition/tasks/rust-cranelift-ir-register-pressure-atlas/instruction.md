Neutron-spectrometer campaign operators must implement fluxpress on the working Rust baseline under /app. fluxpress accrues one spectrometer ring bundle into a residual fluence ledger, then emits a ranked residual-occupancy closure atlas from that ledger alone without re-reading the ring bundle.

Install fluxpress at /app/bin/fluxpress from /app/target/release/fluxpress with exactly two subcommands:

  fluxpress accrue-residuals --campaign <cid> --bundle <name>
  fluxpress emit-occupancy --campaign <cid> --output <path>

accrue-residuals loads the named ring bundle, forms residual channel counts against the campaign background model, quantizes energies and widths, applies coincidence veto gates, and writes one fluence ledger at /app/scratch/ring-fluence/<campaign-id>.json per /app/docs/ring-fluence-ledger-schema.md.

emit-occupancy reads only that ledger for the campaign id and writes a residual-occupancy closure atlas JSON to the caller --output path. Occupancy peak, spill risk, rank ladder, and closure_digest rules live in /app/docs/residual-closure-atlas.md.

Background residuals, quantization, energy order, coincidence veto, and occupancy scan each follow their own lemma doc: /app/docs/residual-lemma.md, /app/docs/micron-ev-quantize.md, /app/docs/energy-order-lemma.md, /app/docs/coincidence-veto-gate.md, /app/docs/occupancy-scan-lemma.md. The two-phase lab workflow, the module wiring in /app/src/lib.rs, and the ledger-only emit boundary appear in /app/docs/fluxpress-workflow.md.

Ring bundles live under /app/fixtures/rings/; inventory is in /app/docs/campaign-ring-catalog.md. Hidden verifier overlays ship under /opt/verifier-fixtures/fluxpress. Micron-eV scale defaults from /app/config/fluxpress.json and may be overridden by TB3_MICRON_EV_SCALE at accrue time; aperture headroom may be overridden by TB3_APERTURE_DELTA at emit time only.

Verifier persistence cases write ledgers such as /app/scratch/ring-fluence/ring-gen.json, /app/scratch/ring-fluence/ring-ref.json, /app/scratch/ring-fluence/ring-sort.json, and /app/scratch/ring-fluence/ring-scale.json. The mid-budget aperture-delta case uses campaign id ring-foxtrot-neg.

Independent verifier reference math lives in /app/scripts/fluxpress_validate.py; pytest helpers live in /app/scripts/campaign_cli.py. The decoy stub at /app/decoy/regatlas_ir_stub.rs sits off the accrue-residuals and emit-occupancy hot path, must never be declared from /app/src/lib.rs, and must stay unused. Do not edit /app/docs/, /app/fixtures/, /app/config/, or /tests/.
