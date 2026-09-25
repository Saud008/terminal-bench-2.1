#!/usr/bin/env bash

glob_match() {
  local pattern="$1"
  local candidate="$2"
  python3 - "$pattern" "$candidate" <<'PY'
import fnmatch, sys
print("true" if fnmatch.fnmatch(sys.argv[2], sys.argv[1]) else "false")
PY
}

candidate_exclude_depth() {
  local rule_path="$1"
  local candidate="$2"
  python3 - "$rule_path" "$candidate" <<'PY'
import os, sys
rule_path, candidate = sys.argv[1:3]
base = os.path.basename(candidate)
print(len(base.split(".")) if base else 0)
PY
}

is_excluded_by_x() {
  local candidate="$1"
  local exclude_depth="$2"
  local x_rules_json="$3"
  local rule_path="$4"
  python3 - "$candidate" "$exclude_depth" "$x_rules_json" "$rule_path" <<'PY'
import json, sys, fnmatch
candidate = sys.argv[1]
limit = int(sys.argv[2])
x_rules = json.loads(sys.argv[3])
rule_path = sys.argv[4]
parent = candidate.rsplit("/", 1)[0] if "/" in candidate else candidate
for row in x_rules:
    pat = row["path"]
    if fnmatch.fnmatch(candidate, pat):
        print("true")
        raise SystemExit
    if limit > 0:
        x_parent = pat.rsplit("/", 1)[0] if "/" in pat else pat
        if parent == x_parent:
            print("true")
            raise SystemExit
print("false")
PY
}

expand_remove_candidates() {
  local rule_path="$1"
  local tree_file="$2"
  python3 - "$rule_path" "$tree_file" <<'PY'
import json, os, sys, fnmatch
rule_path, tree_file = sys.argv[1:3]
anchor = rule_path.split("*", 1)[0].rstrip("/") or "/"
doc = json.load(open(tree_file, encoding="utf-8"))
out = []
for path in sorted(doc["paths"]):
    if not path.startswith(anchor + "/") and path != anchor:
        continue
    rest = path[len(anchor):].lstrip("/")
    if "/" in rest:
        continue
    if fnmatch.fnmatch(os.path.basename(path), "*.tmp") or fnmatch.fnmatch(os.path.basename(path), "*.cache"):
        out.append(path)
print(json.dumps(out))
PY
}
