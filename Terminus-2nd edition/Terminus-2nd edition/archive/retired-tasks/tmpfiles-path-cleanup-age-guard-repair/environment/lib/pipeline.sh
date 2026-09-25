#!/usr/bin/env bash

run_tmpfiles_apply() {
  local scenario="$1"
  local seed="$2"
  local now_epoch="$3"
  local out="$4"

  NOW_EPOCH="$now_epoch"
  local scen_dir="/app/fixtures/scenarios/${scenario}"
  if [[ ! -d "$scen_dir" ]]; then
    scen_dir="$scenario"
  fi
  copy_scenario_tree "$scen_dir"
  local tree_file="${TREE}/tree.json"
  local rules_file="${scen_dir}/rules.conf"
  if [[ ! -f "$rules_file" ]]; then
    echo "missing rules.conf for ${scenario}" >&2
    return 2
  fi

  local rules_json
  rules_json="$(parse_rules_file "$rules_file")"
  local now
  now="$(effective_now)"
  local actions="[]"

  local x_rules
  x_rules="$(python3 - "$rules_json" <<'PY'
import json, sys
rules = json.loads(sys.argv[1])
print(json.dumps([r for r in rules if r["type"] == "x"]))
PY
)"

  local own_phase
  own_phase="$(ownership_phase)"

  if [[ "$own_phase" == "before_remove" ]]; then
    while IFS= read -r row; do
      [[ -z "$row" ]] && continue
      local typ path mode user group
      typ="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["type"])')"
      [[ "$typ" == "o" ]] || continue
      path="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["path"])')"
      mode="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("mode","-"))')"
      user="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("user","-"))')"
      group="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("group","-"))')"
      if [[ "$(apply_ownership "$path" "$mode" "$user" "$group" "$tree_file")" == "ok" ]]; then
        actions="$(python3 - "$actions" "$path" "$user" "$group" <<'PY'
import json, sys
doc = json.loads(sys.argv[1])
doc.append({"type": "ownership", "path": sys.argv[2], "user": sys.argv[3], "group": sys.argv[4]})
print(json.dumps(doc))
PY
)"
      fi
    done < <(echo "$rules_json" | python3 -c 'import json,sys; [print(json.dumps(r)) for r in json.load(sys.stdin)]')
  fi

  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    local typ path mode user group age_sec depth
    typ="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["type"])')"
    path="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["path"])')"
    mode="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("mode","-"))')"
    user="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("user","-"))')"
    group="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("group","-"))')"

    if [[ "$typ" == "r!" ]]; then
      age_sec="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("age") or 0)')"
      depth="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("exclude_depth",0))')"
      local candidates
      candidates="$(expand_remove_candidates "$path" "$tree_file")"
      while IFS= read -r cand; do
        [[ -z "$cand" ]] && continue
        if [[ "$(is_excluded_by_x "$cand" "$depth" "$x_rules" "$path")" == "true" ]]; then
          continue
        fi
        if [[ "$(path_age_eligible "$cand" "$age_sec" "$now" "$tree_file")" == "true" ]]; then
          python3 - "$cand" "$tree_file" <<'PY'
import json, sys
path, tree = sys.argv[1:3]
doc = json.load(open(tree, encoding="utf-8"))
doc["paths"].pop(path, None)
json.dump(doc, open(tree, "w", encoding="utf-8"))
PY
          actions="$(python3 - "$actions" "$cand" <<'PY'
import json, sys
doc = json.loads(sys.argv[1])
doc.append({"type": "remove", "path": sys.argv[2]})
print(json.dumps(doc))
PY
)"
        fi
      done < <(echo "$candidates" | python3 -c 'import json,sys; [print(x) for x in json.load(sys.stdin)]')
    elif [[ "$typ" == "z" ]]; then
      local pending_json
      pending_json="$(pending_under_prefix "$path" "$rules_json" "$tree_file" "$now" "$x_rules")"
      if [[ "$(recreate_allowed "$path" "$pending_json")" == "true" ]]; then
        apply_recreate "$path" "$mode" "$user" "$group" "$tree_file"
        actions="$(python3 - "$actions" "$path" <<'PY'
import json, sys
doc = json.loads(sys.argv[1])
doc.append({"type": "recreate", "path": sys.argv[2]})
print(json.dumps(doc))
PY
)"
      fi
    fi
  done < <(echo "$rules_json" | python3 -c 'import json,sys; [print(json.dumps(r)) for r in json.load(sys.stdin)]')

  if [[ "$own_phase" == "after_remove" ]]; then
    while IFS= read -r row; do
      [[ -z "$row" ]] && continue
      local typ path mode user group
      typ="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["type"])')"
      [[ "$typ" == "o" ]] || continue
      path="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["path"])')"
      mode="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("mode","-"))')"
      user="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("user","-"))')"
      group="$(echo "$row" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("group","-"))')"
      if [[ "$(apply_ownership "$path" "$mode" "$user" "$group" "$tree_file")" == "ok" ]]; then
        actions="$(python3 - "$actions" "$path" "$user" "$group" <<'PY'
import json, sys
doc = json.loads(sys.argv[1])
doc.append({"type": "ownership", "path": sys.argv[2], "user": sys.argv[3], "group": sys.argv[4]})
print(json.dumps(doc))
PY
)"
      fi
    done < <(echo "$rules_json" | python3 -c 'import json,sys; [print(json.dumps(r)) for r in json.load(sys.stdin)]')
  fi

  write_apply_export "$scenario" "$seed" "$now" "$tree_file" "$actions" "$out"
}

run_tmpfiles_generate() {
  local scenario="$1"
  local mode="$2"
  local out="$3"
  local scen_dir="/app/fixtures/scenarios/${scenario}"
  if [[ ! -d "$scen_dir" ]]; then
    scen_dir="$scenario"
  fi
  local frag_dir="${scen_dir}/fragments"
  local merged="/tmp/tmpfiles-merged-${scenario}-${mode}.conf"
  write_merged_rules "$frag_dir" "$mode" "$merged"
  write_generate_export "$scenario" "$mode" "$merged" "$out"
}

pending_under_prefix() {
  local prefix="$1"
  local rules_json="$2"
  local tree_file="$3"
  local now="$4"
  local x_rules="$5"
  python3 - "$prefix" "$rules_json" "$tree_file" "$now" "$x_rules" <<'PY'
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

def age_eligible(meta, age_sec, now, use_mtime=False):
    if use_mtime:
        stamp = int(meta.get("mtime", 0))
    else:
        stamp = max(int(meta.get("atime", 0)), int(meta.get("btime", 0)))
    return now - stamp >= age_sec

prefix, rules_json, tree_file, now, x_rules = sys.argv[1:6]
prefix = prefix.rstrip("/") or "/"
now = int(now)
rules = json.loads(rules_json)
x_rules = json.loads(x_rules)
tree = json.load(open(tree_file, encoding="utf-8"))
pending = []
for rule in rules:
    if rule["type"] != "r!":
        continue
    age_sec = rule.get("age") or 0
    glob_pat = rule["path"]
    for path, meta in tree["paths"].items():
        if not path.startswith(prefix + "/") and path != prefix:
            continue
        if not globstar_match(glob_pat, path):
            continue
        depth = relative_depth(anchor_dir(glob_pat), path)
        excluded = False
        for x in x_rules:
            if globstar_match(x["path"], path) and depth <= rule.get("exclude_depth", 0):
                excluded = True
                break
        if excluded:
            continue
        if age_eligible(meta, age_sec, now):
            pending.append(path)
print(json.dumps(sorted(pending)))
PY
}
