#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="${ROOT_DIR}/files/modules"

install -d -m 0755 /app/lib/ruleio /app/lib/bindio /app/lib/snapio /app/lib/planio

cp -f "${MODULE_DIR}/udvp-order-precedence.sh" /app/lib/ruleio/order_rules.sh
cp -f "${MODULE_DIR}/udvp-attr-chain.sh" /app/lib/bindio/inherit_attrs.sh
cp -f "${MODULE_DIR}/udvp-modalias-glob.sh" /app/lib/bindio/bind_tsv.sh
cp -f "${MODULE_DIR}/udvp-ledger-writer.sh" /app/lib/snapio/snap_writer.sh
cp -f "${MODULE_DIR}/udvp-symlink-arbitration.sh" /app/lib/planio/alias_arb.sh
cp -f "${MODULE_DIR}/udvp-perm-matrix.sh" /app/lib/planio/owner_lane.sh
cp -f "${MODULE_DIR}/udvp-emit-matrix.sh" /app/lib/planio/device_rows.sh

chmod +x /app/lib/ruleio/order_rules.sh \
  /app/lib/bindio/inherit_attrs.sh \
  /app/lib/bindio/bind_tsv.sh \
  /app/lib/snapio/snap_writer.sh \
  /app/lib/planio/alias_arb.sh \
  /app/lib/planio/owner_lane.sh \
  /app/lib/planio/device_rows.sh

_udvp_verify_layout() {
  local f
  for f in \
    lib/ruleio/order_rules.sh \
    lib/bindio/inherit_attrs.sh \
    lib/bindio/bind_tsv.sh \
    lib/snapio/snap_writer.sh \
    lib/planio/alias_arb.sh \
    lib/planio/owner_lane.sh \
    lib/planio/device_rows.sh
  do
    if [[ ! -s "/app/$f" ]]; then
      echo "missing oracle layout: /app/$f" >&2
      return 1
    fi
  done
  if ! grep -q 'sort_by(.priority' /app/lib/ruleio/order_rules.sh; then
    echo "order_rules module not applied" >&2
    return 1
  fi
  if ! grep -q 'build_inherited_map' /app/lib/snapio/snap_writer.sh; then
    echo "staging digest module not applied" >&2
    return 1
  fi
  if ! grep -q 'reverse' /app/lib/planio/owner_lane.sh; then
    echo "permission precedence module not applied" >&2
    return 1
  fi
  return 0
}
_udvp_verify_layout

python3 <<'PY'
import pathlib

def must_contain(path: str, needle: str) -> None:
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if needle not in text:
        raise SystemExit(f"missing {needle!r} in {path}")

must_contain("/app/lib/ruleio/order_rules.sh", "sort_by(.priority")
must_contain("/app/lib/bindio/inherit_attrs.sh", "build_inherited_map")
must_contain("/app/lib/bindio/bind_tsv.sh", "glob_match")
must_contain("/app/lib/snapio/snap_writer.sh", "staging_digest")
must_contain("/app/lib/planio/alias_arb.sh", "SYMLINK")
must_contain("/app/lib/planio/owner_lane.sh", "reverse")
must_contain("/app/lib/planio/device_rows.sh", "plan_digest")
for rel in (
    "lib/ruleio/order_rules.sh",
    "lib/bindio/inherit_attrs.sh",
    "lib/bindio/bind_tsv.sh",
    "lib/snapio/snap_writer.sh",
    "lib/planio/alias_arb.sh",
    "lib/planio/owner_lane.sh",
    "lib/planio/device_rows.sh",
):
    p = pathlib.Path("/app") / rel
    if not p.is_file() or p.stat().st_size < 10:
        raise SystemExit(f"oracle layout empty: {p}")
    if not p.read_text(encoding="utf-8").strip():
        raise SystemExit(f"oracle layout blank: {p}")
staging = pathlib.Path("/app/state")
output = pathlib.Path("/app/output")
staging.mkdir(parents=True, exist_ok=True)
output.mkdir(parents=True, exist_ok=True)
print("udvp oracle module contract checks ok")
PY

bash /app/scripts/rebuild-udevplan.sh
test -x /app/bin/udev-policy-planner
echo "udev-policy-planner oracle ready"
