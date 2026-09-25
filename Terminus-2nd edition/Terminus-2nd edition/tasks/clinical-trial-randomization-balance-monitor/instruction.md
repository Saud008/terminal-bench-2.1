Task identity d87c935e1e defines the engineering problem for clinical trial randomization balance monitor. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Clinical trial biostatistics labs run numerical simulation over enrollment chronicles to publish calibration closure reports that quantify trial-arm imbalance under stratified permuted-block protocols. Operators run rtbalctl on the working Rust baseline under /app to monitor randomized balance from enrollment logs, using reference math for skew metrics and deterministic trial closure before the imbalance ledger is emitted.

Install rtbalctl at /app/bin/rtbalctl with these subcommands:

  rtbalctl compile-trial --trial <id> [--root D]
  rtbalctl accept-log --trial <id> [--root D]
  rtbalctl run-balance --trial <id> [--root D]
  rtbalctl emit-closure --trial <id> --out <path> [--root D]

rtbalctl compile-trial reads the trial manifest and writes /app/state/trial-latch.json containing a deterministic manifest fingerprint and trial metadata without enrollment bodies. Latch field rules and preimage rank ladder appear in /app/docs/trial-latch-schema.md.

rtbalctl accept-log normalizes the enrollment NDJSON chronicle into /app/work/enrollment-chronicle.json with ts then seq chronology, deduplicated subject events, and normalized row counts. Chronology normalization and dedupe policy appear in /app/docs/enrollment-chronicle-normalization.md.

rtbalctl run-balance applies stratification factor keys from canonical sorted JSON factor maps, stratified arm assignment per stratum with seeded block sizes, venue enrollment caps counting active enrollments only, and withdrawal handling that removes participants from active tallies while retaining assignment history. Stratification keys, block permutation seeds, and venue cap rules appear in /app/docs/stratified-block-randomization.md and /app/docs/venue-cap-active-policy.md.

rtbalctl emit-closure writes imbalance closure JSON to the caller-provided --out path with per_stratum active arm counts, max_skew, venues_at_cap, open_slots, and closure fingerprint. Field definitions appear in /app/docs/balance-closure-schema.md.

Bundled trials, logs, and venue cap tables live under /app/fixtures/. Trial inventory and exercised behaviors appear in /app/docs/trial-fixture-catalog.md. Runtime-supplied fixture roots honor TB3_FIXTURE_DIR. Trial build randomization honors RTBAL_TRIAL_SEED if present in the environment.

Compile rtbalctl with /usr/local/cargo/bin/cargo build --release --locked from /app. Cargo writes /app/target/release/rtbalctl before installation to /app/bin/rtbalctl. Run /app/scripts/reset-state.sh before cross-run verifier cases. Pytest invokes rtbalctl via subprocess after cargo rebuild. Independent reference math lives in tests/rtbal_refmath.py using the Python hashlib module. Verifier helpers live in tests/rtbal_helpers.py. Behavioral cases are split across tests/test_rtbal_compile.py, tests/test_rtbal_accept.py, tests/test_rtbal_balance.py, tests/test_rtbal_closure.py, and tests/test_rtbal_hidden.py and are collected through tests/test_outputs.py. The decoy sample_size_prior module is not used by compile-trial, accept-log, run-balance, or emit-closure.
