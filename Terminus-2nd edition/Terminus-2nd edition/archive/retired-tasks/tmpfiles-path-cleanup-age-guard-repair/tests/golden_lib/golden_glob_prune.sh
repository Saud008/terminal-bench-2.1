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
import os, sys, re
rule_path, candidate = sys.argv[1:3]
before = rule_path.split("*", 1)[0]
anchor = os.path.normpath(before.rstrip("/")) or "/"
cand = candidate.rstrip("/")
if not cand.startswith(anchor):
    print(0)
    raise SystemExit
rest = cand[len(anchor):].lstrip("/")
print(len(rest.split("/")) if rest else 0)
PY
}

is_excluded_by_x() {
  local candidate="$1"
  local exclude_depth="$2"
  local x_rules_json="$3"
  local rule_path="$4"
  python3 - "$candidate" "$exclude_depth" "$x_rules_json" "$rule_path" <<'PY'
import json, sys, fnmatch, re, os

def globstar_match(pattern, candidate):
    if "**" in pattern:
        regex = "^" + re.escape(pattern).replace("\\*\\*", ".*").replace("\\*", "[^/]*") + "$"
        return re.match(regex, candidate) is not None
    return fnmatch.fnmatch(candidate, pattern)

def anchor_dir(glob_pattern):
    before_star = glob_pattern.split("*", 1)[0]
    return os.path.normpath(before_star.rstrip("/")) or "/"

def relative_depth(anchor, candidate):
    anchor = anchor.rstrip("/") or "/"
    cand = candidate.rstrip("/")
    if not cand.startswith(anchor):
        return 0
    rest = cand[len(anchor):].lstrip("/")
    if not rest:
        return 0
    return len(rest.split("/"))

candidate = sys.argv[1]
limit = int(sys.argv[2])
x_rules = json.loads(sys.argv[3])
rule_path = sys.argv[4]
depth = relative_depth(anchor_dir(rule_path), candidate)
for row in x_rules:
    pat = row["path"]
    if globstar_match(pat, candidate) and depth <= limit:
        print("true")
        raise SystemExit
print("false")
PY
}

expand_remove_candidates() {
  local rule_path="$1"
  local tree_file="$2"
  python3 - "$rule_path" "$tree_file" <<'PY'
import json, sys, fnmatch, re

def globstar_match(pattern, candidate):
    if "**" in pattern:
        regex = "^" + re.escape(pattern).replace("\\*\\*", ".*").replace("\\*", "[^/]*") + "$"
        return re.match(regex, candidate) is not None
    return fnmatch.fnmatch(candidate, pattern)

rule_path, tree_file = sys.argv[1:3]
doc = json.load(open(tree_file, encoding="utf-8"))
out = []
for path in sorted(doc["paths"]):
    if globstar_match(rule_path, path):
        out.append(path)
print(json.dumps(out))
PY
}
