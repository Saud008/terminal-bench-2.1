#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

pick_ticket_id() {
  local tickets_path="$1"
  local profile_id="$2"
  local batch_id="$3"
  local as_of="$4"
  python3 - "${tickets_path}" "${profile_id}" "${batch_id}" "${as_of}" <<'PY'
import json, sys
from pathlib import Path

doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
profile_id = sys.argv[2]
batch_id = sys.argv[3]
as_of = int(sys.argv[4])
hits = []
for ticket in doc.get("tickets", []):
    if str(ticket.get("profile_id")) != profile_id:
        continue
    if str(ticket.get("paper_batch_id")) != batch_id:
        continue
    start = int(ticket.get("valid_from_epoch", 0))
    end = int(ticket.get("valid_until_epoch", 0))
    if as_of >= start and as_of <= end:
        hits.append(str(ticket.get("ticket_id", "")))
if not hits:
    print("")
else:
    print(sorted(hits)[0])
PY
}
