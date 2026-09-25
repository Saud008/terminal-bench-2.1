# Oracle solve — task identity clinical-trial-randomization-balance-monitor token d87c935e
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

rm -rf /app/target
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/rtbalctl /app/bin/rtbalctl
bash /app/scripts/reset-state.sh
test -x /app/bin/rtbalctl
grep -q 'abs_diff' /app/closure/imbalance_ledger.rs
grep -q 'protocol_version' /app/manifest/trial_digest.rs
echo "clinical-trial-randomization-balance-monitor oracle ready"
