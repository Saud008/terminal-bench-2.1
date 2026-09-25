#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/files/checksum.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "solution/files/checksum.rs not found" >&2; exit 1; }

F="${SOL_DIR}/files"
cp -f "${F}/checksum.rs" /app/crates/nmeapipeline/src/checksum.rs
cp -f "${F}/fields.rs" /app/crates/nmeapipeline/src/parse/fields.rs
cp -f "${F}/normalize.rs" /app/crates/nmeapipeline/src/talker/normalize.rs
cp -f "${F}/multipart.rs" /app/crates/nmeapipeline/src/merge/multipart.rs
cp -f "${F}/datetime.rs" /app/crates/nmeapipeline/src/merge/datetime.rs
cp -f "${F}/compose.rs" /app/crates/nmeapipeline/src/merge/compose.rs
cp -f "${F}/rmc.rs" /app/crates/nmeapipeline/src/context/rmc.rs
cp -f "${F}/reconcile.rs" /app/crates/nmeapipeline/src/session/reconcile.rs
cp -f "${F}/pending.rs" /app/crates/nmeapipeline/src/session/pending.rs
cp -f "${F}/validate.rs" /app/crates/nmeapipeline/src/export/validate.rs
cp -f "${F}/writer.rs" /app/crates/nmeapipeline/src/export/writer.rs
cp -f "${F}/wrap.rs" /app/crates/nmeapipeline/src/export/wrap.rs
cp -f "${F}/staging.rs" /app/crates/nmeapipeline/src/export/staging.rs

find /app/crates -name '*.rs' -exec sed -i 's/\r$//' {} +

cargo build --release --locked -p nmeapipeline
install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline
bash /app/scripts/reset-state.sh
nmeapipeline merge --input /app/fixtures/streams/baseline.nmea --output /app/output/merge-report.json
