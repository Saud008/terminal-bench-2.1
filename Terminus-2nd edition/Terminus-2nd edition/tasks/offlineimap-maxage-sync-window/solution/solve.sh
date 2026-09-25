#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}/patches" "${SCRIPT_DIR}" "/solution/patches" "/solution" "/oracle/solution/patches" "/oracle/solution" "/task/solution/patches" "/task/solution"; do
  if [[ -f "${candidate}/golden_sync.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

[[ -n "${SOL_DIR}" ]] || { echo "golden_sync.sh not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_sync.sh" "/app/lib/offlineimap/sync.sh"
cp -f "${SOL_DIR}/golden_cache_ledger.sh" "/app/lib/offlineimap/cache_ledger.sh"
cp -f "${SOL_DIR}/golden_state_writer.sh" "/app/lib/offlineimap/state_writer.sh"
cp -f "${SOL_DIR}/golden_publish.sh" "/app/lib/offlineimap/staging/publish.sh"
cp -f "${SOL_DIR}/golden_maxage.awk" "/app/lib/offlineimap/maxage.awk"
cp -f "${SOL_DIR}/golden_folder_filter.awk" "/app/lib/offlineimap/folder_filter.awk"
cp -f "${SOL_DIR}/golden_summary.awk" "/app/lib/offlineimap/export/summary.awk"

sed -i 's/\r$//' \
  "/app/lib/offlineimap/sync.sh" \
  "/app/lib/offlineimap/cache_ledger.sh" \
  "/app/lib/offlineimap/state_writer.sh" \
  "/app/lib/offlineimap/staging/publish.sh" \
  "/app/lib/offlineimap/maxage.awk" \
  "/app/lib/offlineimap/folder_filter.awk" \
  "/app/lib/offlineimap/export/summary.awk"

make -C "/app" install
bash "/app/scripts/reset-state.sh"
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

app = Path("/app")
catalog = json.loads((app / "fixtures" / "catalog.json").read_text())
cli = [str(app / "bin" / "offlineimap-audit"), "sync"]
for entry in catalog["scenarios"]:
    name = entry["name"]
    sdir = app / "fixtures" / "scenarios" / name
    export = app / "output" / f"{name}.json"
    cmd = cli + [
        "--mailbox-dir", str(sdir),
        "--imap-meta", str(sdir / "imap-meta.json"),
        "--folder-rules", str(sdir / "folder.rules"),
        "--reference-epoch", str(entry["reference_epoch"]),
        "--maxage-sec", str(entry["maxage_sec"]),
        "--tz-offset", str(entry["tz_offset"]),
        "--export", str(export),
    ]
    subprocess.run(cmd, check=True, cwd=app)
PY
