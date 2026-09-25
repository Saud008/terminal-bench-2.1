# Pytest verifier primitives

Contract helpers live in tests/kiln_balance_verifier.py alongside the kilnbal subprocess driver in tests/kiln_cli_runner.py.

Tests recompute thermodynamic balance math independently using Python hashlib and random modules per this contract. Use hashlib.sha256 for digest checks matching heat-ledger-fields.md. Randomized anti-hardcoding rows draw fuel labels and masses with random.Random seeds declared in pytest cases.

Verifier fixture roots include /app/fixtures/kiln-runs/, /app/state/tele-buffer/, /app/work/fuel-buffer/, /app/work/probe-grid/, /app/work/balance-scratch/, and /app/output/ for published heat balance ledgers.

Randomized anti-hardcoding pytest cases write ephemeral CSV files under /app/work/ named rand-fuel.csv, rand-k.csv, rand-ts.csv, rand-ts-fuel.csv, and rand-ts-clinker.csv. Example run identifiers include bind-fuel-energy, ledger-clinker-sum, ledger-multi-fuel, and ledger-rand-fuel. Published ledger filenames follow the pattern <run-id>-heat-balance-ledger.json under /app/output/. Hidden calibration bundles use TB3_FIXTURE_ROOT=/opt/verifier-fixtures/kilnbal/kiln-runs and TB3_CAL_TABLE=/opt/verifier-fixtures/kilnbal/kiln-runs/tb3-cal-offset/cal_table.csv when overrides apply.
