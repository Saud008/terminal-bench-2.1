#!/usr/bin/env bash
# Classify parsed porcelain records using export config.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

wt_classify_entries() {
  local raw_json="$1"
  local config_path="$2"
  wt_require_file "${config_path}"
  python3 - "${raw_json}" "${config_path}" <<'PY'
import json
import sys

raw = json.loads(sys.argv[1])
cfg = json.loads(open(sys.argv[2], encoding="utf-8").read())
threshold = int(cfg["rename_score_min"])

MODES_ORD = ("mH", "mI", "mW")
MODES_UNM = ("m1", "m2", "m3", "mW")


def is_submodule(record: dict) -> bool:
    keys = MODES_UNM if record["tag"] == "u" else MODES_ORD
    return any(record.get(k) == "160000" for k in keys)


entries = []
for rec in raw:
    tag = rec["tag"]
    if tag == "1":
        entry = {
            "kind": "ordinary",
            "xy": rec["xy"],
            "path": rec["path"],
            "submodule": is_submodule(rec),
            "index_mode": rec["mI"],
            "worktree_mode": rec["mW"],
        }
        entries.append(entry)
    elif tag == "2":
        if rec["score"] < threshold:
            continue
        kind = "rename" if rec["letter"] == "R" else "copy"
        entry = {
            "kind": kind,
            "xy": rec["xy"],
            "path": rec["path"],
            "old_path": rec["old_path"],
            "score": rec["score"],
            "submodule": is_submodule(rec),
            "index_mode": rec["mI"],
            "worktree_mode": rec["mW"],
        }
        entries.append(entry)
    elif tag == "u":
        entry = {
            "kind": "unmerged",
            "xy": rec["xy"],
            "path": rec["path"],
            "submodule": is_submodule(rec),
            "worktree_mode": rec["mW"],
            "unmerged_xy": rec["xy"],
        }
        entries.append(entry)
    elif tag == "?":
        entries.append(
            {
                "kind": "untracked",
                "xy": "..",
                "path": rec["path"],
                "submodule": False,
            }
        )
    elif tag == "!":
        entries.append(
            {
                "kind": "ignored",
                "xy": "..",
                "path": rec["path"],
                "submodule": False,
            }
        )

entries.sort(key=lambda e: e["path"].encode("utf-8"))
print(json.dumps(entries, separators=(",", ":")))
PY
}
