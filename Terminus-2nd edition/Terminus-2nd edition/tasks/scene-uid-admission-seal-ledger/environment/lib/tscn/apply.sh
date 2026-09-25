#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=remap.sh
source "$(dirname "${BASH_SOURCE[0]}")/remap.sh"
# shellcheck source=merge.sh
source "$(dirname "${BASH_SOURCE[0]}")/merge.sh"
# shellcheck source=graph.sh
source "$(dirname "${BASH_SOURCE[0]}")/graph.sh"
# shellcheck source=ledger.sh
source "$(dirname "${BASH_SOURCE[0]}")/ledger.sh"
# shellcheck source=orphan.sh
source "$(dirname "${BASH_SOURCE[0]}")/orphan.sh"

tscn_apply_remap_shell() {
  local content="$1" remap_json="$2"
  tscn_apply_remap_to_text "${content}" "${remap_json}"
}

tscn_apply_merge_python() {
  local tree="$1" tree_json="$2" remap_json="$3" base_name="$4" left_name="$5" right_name="$6"
  python3 - "${tree}" "${tree_json}" "${remap_json}" "${base_name}" "${left_name}" "${right_name}" <<'PY'
import json, os, subprocess, sys
from pathlib import Path

tree = Path(sys.argv[1])
tree_meta = json.loads(sys.argv[2])
remap = json.loads(sys.argv[3])
base_name, left_name, right_name = sys.argv[4], sys.argv[5], sys.argv[6]
root = os.environ.get("TSCN_APP_ROOT", "/app")
lib = Path(root) / "lib" / "tscn"

def read_branch(branch, rel):
    p = tree / branch / rel
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")

def shell_remap(text, remap):
    env = {
        **os.environ,
        "TSCN_APP_ROOT": root,
        "TSCN_CONTENT": text,
        "TSCN_REMAP_JSON": json.dumps(remap),
    }
    proc = subprocess.run(
        [
            "bash", "-c",
            f'source "{lib}/common.sh"; source "{lib}/remap.sh"; '
            'tscn_apply_remap_to_text "$TSCN_CONTENT" "$TSCN_REMAP_JSON"',
        ],
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return proc.stdout

def shell_merge(base_t, left_t, right_t, base_p, left_p, right_p, base_branch):
    env = {
        **os.environ,
        "TSCN_APP_ROOT": root,
        "TSCN_BASE_TEXT": base_t,
        "TSCN_LEFT_TEXT": left_t,
        "TSCN_RIGHT_TEXT": right_t,
        "TSCN_BASE_PATH": base_p,
        "TSCN_LEFT_PATH": left_p,
        "TSCN_RIGHT_PATH": right_p,
        "TSCN_BASE_NAME": base_branch,
    }
    proc = subprocess.run(
        [
            "bash", "-c",
            f'source "{lib}/common.sh"; source "{lib}/merge.sh"; '
            'tscn_merge_three_way "$TSCN_BASE_TEXT" "$TSCN_LEFT_TEXT" "$TSCN_RIGHT_TEXT" '
            '"$TSCN_BASE_PATH" "$TSCN_LEFT_PATH" "$TSCN_RIGHT_PATH" "$TSCN_BASE_NAME"',
        ],
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return proc.stdout

merged = {}
for rel in tree_meta.get("files", []):
    if rel in tree_meta.get("delete_on_merge", []):
        continue
    base_t = shell_remap(read_branch(base_name, rel), remap)
    left_t = shell_remap(read_branch(left_name, rel), remap)
    right_t = shell_remap(read_branch(right_name, rel), remap)
    out = shell_merge(
        base_t,
        left_t,
        right_t,
        str(tree / base_name / rel),
        str(tree / left_name / rel),
        str(tree / right_name / rel),
        base_name,
    )
    merged[rel] = out.replace("\r\n", "\n").replace("\r", "\n")
print(json.dumps(merged))
PY
}

tscn_apply_merge() {
  local tree="$1" base_name="$2" left_name="$3" right_name="$4" seed="$5"
  local tree_json remap_json merged_json graph_json ledger_json orphans payload
  tree_json="$(tscn_load_json "${tree}/tree.json")"
  remap_json="$(tscn_load_remap_table "${tree}" "${seed}")"
  merged_json="$(tscn_apply_merge_python "${tree}" "${tree_json}" "${remap_json}" "${base_name}" "${left_name}" "${right_name}")"
  graph_json="$(tscn_analyze_uid_graph "${merged_json}")"
  ledger_json="$(tscn_build_ledger "${merged_json}")"
  orphans="$(tscn_find_orphans "${merged_json}")"
  payload="$(python3 - "${tree}" "${base_name}" "${left_name}" "${right_name}" "${seed}" "${merged_json}" "${graph_json}" "${ledger_json}" "${orphans}" <<'PY'
import json, sys
graph = json.loads(sys.argv[7])
payload = {
    "tree": sys.argv[1],
    "base": sys.argv[2],
    "left": sys.argv[3],
    "right": sys.argv[4],
    "seed": int(sys.argv[5]),
    "merged_files": json.loads(sys.argv[6]),
    "uid_graph_ok": graph["uid_graph_ok"],
    "cycles": graph["cycles"],
    "orphans": json.loads(sys.argv[9]),
    "ledger": json.loads(sys.argv[8]),
}
print(json.dumps(payload))
PY
)"
  echo "${payload}"
}

tscn_apply_exit_code() {
  local payload="$1"
  python3 - "${payload}" <<'PY'
import json, sys
payload = json.loads(sys.argv[1])
print(2 if not payload.get("uid_graph_ok", True) else 0)
PY
}
