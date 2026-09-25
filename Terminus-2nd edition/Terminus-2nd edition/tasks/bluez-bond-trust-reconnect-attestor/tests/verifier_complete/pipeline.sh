#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh
source /app/lib/intake/trace_loader.sh
source /app/lib/intake/device_table.sh
source /app/lib/trustgate/pairing_gate.sh
source /app/lib/trustgate/resume_clear.sh
source /app/lib/trustgate/disconnect_capture.sh
source /app/lib/trustgate/gatt_identity.sh
source /app/lib/trustgate/battery_debounce.sh

_payload_nonempty() {
  [[ -n "${1:-}" ]]
}

_event_op() {
  local payload="$1"
  printf '%s' "$payload" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["op"])'
}

_dispatch_in_trace_order() {
  local line="$1"
  if ! _payload_nonempty "$line"; then
    return 0
  fi
  dispatch_event "$line"
}

dispatch_event() {
  local payload="$1"
  if ! _payload_nonempty "$payload"; then
    return 0
  fi
  eval "$(python3 - "$payload" <<'PY'
import json, shlex, sys

ev = json.loads(sys.argv[1])
op = ev["op"]
mac = ev.get("mac", "")


def cmd(*parts):
    return " ".join(shlex.quote(str(p)) for p in parts)


if op == "seed_bond":
    print(cmd("seed_bond", mac, ev.get("addr_type", "public"), str(ev.get("trusted", False)).lower(), ev.get("resume_token", "")))
elif op == "pairing_confirm":
    print(cmd("pairing_confirm", mac))
elif op == "connect":
    print(cmd("connect_device", mac, ev.get("addr_type", "public")))
elif op == "disconnect":
    print(cmd("record_disconnect", mac, ev.get("reason", "unknown")))
elif op == "bond_remove":
    print(cmd("bond_remove_ledger", mac))
elif op == "adapter_power":
    print(cmd("set_adapter_power", ev.get("state", "on")))
elif op == "gatt_discover":
    print(cmd("gatt_discover", mac, ev["uuid"]))
elif op == "battery_level":
    print(cmd("battery_level", mac, str(int(ev.get("ts", 0)))))
else:
    raise SystemExit(f"unknown op: {op}")
PY
)"
}

write_midstate() {
  local seed="$1" trace_path="$2" midstate="$3"
  python3 - "$seed" "$trace_path" "$midstate" "${STATE_DIR}" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

seed, trace_path, midstate_path, state_dir = sys.argv[1:5]
counters = json.load(open(Path(state_dir) / "counters.json", encoding="utf-8"))
adapter = (Path(state_dir) / "adapter_power.txt").read_text(encoding="utf-8").strip()
disconnect = json.load(open(Path(state_dir) / "disconnect_reasons.json", encoding="utf-8"))
ledger_rows = []
for raw in open(Path(state_dir) / "ledger_rows.jsonl", encoding="utf-8"):
    line = raw.strip()
    if line:
        ledger_rows.append(json.loads(line))
trace_name = Path(trace_path).name

payload = "\n".join(
    [
        f"seed={seed}",
        f"trace={trace_name}",
        f"adapter_power={adapter}",
        f"pairing_confirms={int(counters.get('pairing_confirms', 0))}",
        f"resume_tokens_cleared={int(counters.get('resume_tokens_cleared', 0))}",
        f"gatt_resolve_count={int(counters.get('gatt_resolve_count', 0))}",
        f"reconnect_attempts={int(counters.get('reconnect_attempts', 0))}",
        "disconnect_reasons=" + json.dumps(disconnect, separators=(",", ":")),
    ]
)
midstate_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

doc = {
    "schema_version": 1,
    "seed": seed,
    "trace": trace_name,
    "adapter_power": adapter,
    "pairing_confirms": int(counters.get("pairing_confirms", 0)),
    "resume_tokens_cleared": int(counters.get("resume_tokens_cleared", 0)),
    "gatt_resolve_count": int(counters.get("gatt_resolve_count", 0)),
    "reconnect_attempts": int(counters.get("reconnect_attempts", 0)),
    "disconnect_reasons": disconnect,
    "ledger_rows": ledger_rows,
    "midstate_digest": midstate_digest,
}
Path(midstate_path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

run_absorb() {
  local trace_arg="$1" config="$2" seed="$3" midstate="$4"
  local trace rows_file
  trace="$(resolve_trace_path "$trace_arg")"
  init_run_state
  load_debounce_ms "$config"

  rows_file="${STATE_DIR}/rows.jsonl"
  sorted_trace_rows "$trace" > "$rows_file"

  local line
  while IFS= read -r line; do
    _dispatch_in_trace_order "$line"
  done < "$rows_file"

  write_midstate "$seed" "$trace" "$midstate"
}
