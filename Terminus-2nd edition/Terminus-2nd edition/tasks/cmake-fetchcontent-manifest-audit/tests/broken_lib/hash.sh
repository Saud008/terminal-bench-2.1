#!/usr/bin/env bash
# FetchContent tarball + pin audit (broken: GIT_TAG pins, extracted-content hash).

hash_audit_deps() {
  local tree_json="$1"
  local vendor_dir="$2"
  local pins_file="$3"
  local out="$4"

  # shellcheck disable=SC1090
  source "$pins_file"

  local failures=() dep_lines=()
  local name url hash archive actual pin_val ok

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    url=$(python3 - <<PY
import json
tree=json.load(open("${tree_json}"))
for f in tree["files"]:
  for dep in f.get("fetchcontent", []):
    if dep["name"] == "${name}":
      print(dep.get("url",""))
      raise SystemExit
print("")
PY
)
    hash=$(python3 - <<PY
import json
tree=json.load(open("${tree_json}"))
for f in tree["files"]:
  for dep in f.get("fetchcontent", []):
    if dep["name"] == "${name}":
      print(dep.get("url_hash",""))
      raise SystemExit
print("")
PY
)
    archive="$url"
    local tmpdir
    tmpdir=$(mktemp -d)
    tar -xzf "${vendor_dir}/${archive}" -C "$tmpdir"
    actual=$(find "$tmpdir" -type f -print0 | sort -z | xargs -0 cat | sha256sum | awk '{print $1}')
    rm -rf "$tmpdir"

    local upper="${name^^}"
    pin_val=""
    eval "pin_val=\${PIN_${upper}_GIT_TAG:-}"

    ok="false"
    if [[ "$actual" == "$hash" && "$actual" == "$pin_val" ]]; then
      ok="true"
    else
      failures+=("$name")
    fi
    dep_lines+=("{\"name\":\"${name}\",\"archive\":\"${archive}\",\"url_hash_expected\":\"${hash}\",\"url_hash_actual\":\"${actual}\",\"pin_field\":\"git_commit\",\"pin_value\":\"${pin_val}\",\"ok\":${ok}}")
  done < <(python3 - <<PY
import json
names=set()
for f in json.load(open("${tree_json}"))["files"]:
  for dep in f.get("fetchcontent", []):
    names.add(dep["name"])
for n in sorted(names):
  print(n)
PY
)

  {
    echo '{'
    echo '  "deps": ['
    local i=0
    for line in "${dep_lines[@]}"; do
      [[ $i -gt 0 ]] && echo ','
      echo -n "    ${line}"
      i=$((i + 1))
    done
    echo
    echo '  ],'
    echo -n '  "failures": ['
    local sep=""
    for f in "${failures[@]}"; do
      echo -n "${sep}\"${f}\""
      sep=", "
    done
    echo ']'
    echo '}'
  } > "$out"
}
