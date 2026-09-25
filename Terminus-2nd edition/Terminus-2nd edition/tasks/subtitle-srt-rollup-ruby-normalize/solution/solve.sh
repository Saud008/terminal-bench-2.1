# Oracle solve — task identity subtitle-srt-rollup-ruby-normalize token d5b4e8fd
#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_runner.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_runner.rs not found" >&2; exit 1; }

DEST="${APP_ROOT}/crates/srt-core/src"
cp -f "${SOL}/golden_runner.rs" "${DEST}/runner.rs"
cp -f "${SOL}/golden_ledger.rs" "${DEST}/ledger.rs"
cp -f "${SOL}/golden_publish.rs" "${DEST}/publish.rs"
cp -f "${SOL}/golden_parser.rs" "${DEST}/parser.rs"
cp -f "${SOL}/golden_ruby.rs" "${DEST}/ruby.rs"
cp -f "${SOL}/golden_timeline.rs" "${DEST}/ssrrn_timeline.rs"
cp -f "${SOL}/golden_rollup.rs" "${DEST}/rollup.rs"

cd "${APP_ROOT}"
cargo build --offline --release --locked -p srtctl
# Agent sessions cannot refresh /usr/local/bin; verifier install runs as root.
if [ "$(id -u)" -eq 0 ] && [ -w /usr/local/bin ]; then
  install -o root -g root -m 0755 "${APP_ROOT}/target/release/srtctl" /usr/local/bin/srtctl
fi
bash /app/scripts/reset-state.sh
