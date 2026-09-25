#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/dn/normalize.sh"

parse_acl_rule_line() {
  python3 - "$1" <<'PY'
import re, sys

def normalize_dn(dn):
    parts = []
    for rdn in dn.split(","):
        rdn = rdn.strip()
        if not rdn:
            continue
        if "=" in rdn:
            a, v = rdn.split("=", 1)
            parts.append(f"{a.strip().lower()}={v.strip()}")
        else:
            parts.append(rdn.lower())
    return ",".join(parts)

line = sys.argv[1].strip()
if not (line.startswith("ALLOW ") or line.startswith("DENY ")):
    sys.exit(1)
effect = "allow" if line.startswith("ALLOW ") else "deny"
body = line.split(None, 1)[1]
left, attrs_part = body.split(" ATTR ", 1)
attrs = ",".join(a.strip() for a in attrs_part.split(","))
m = re.match(
    r"(group|user)\s+(.+?)\s+((?:read|write|search|delete|compare)(?:,(?:read|write|search|delete|compare))*)$",
    left.strip(),
    re.I,
)
if not m:
    sys.exit(1)
print(f"{effect}|{m.group(1).lower()}|{normalize_dn(m.group(2).strip())}|{m.group(3)}|{attrs}")
PY
}

parse_acl_directory() {
  local dir="$1"
  local f line block_target="" block_scope="" block_inherit="yes" block_id=0
  shopt -s nullglob
  for f in "$dir"/*.acl; do
    [[ -f "$f" ]] || continue
    local src base
    base="$(basename "$f" .acl)"
    block_target="" block_scope="subtree" block_inherit="yes"
    local -a rules=()
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" || "$line" == \#* ]] && continue
      if [[ "$line" == "---" ]]; then
        emit_acl_block "$base" "$block_id" "$block_target" "$block_scope" "$block_inherit" "${rules[@]}"
        rules=()
        block_target="" block_scope="subtree" block_inherit="yes"
        block_id=$((block_id + 1))
        continue
      fi
      if [[ "$line" == TARGET* ]]; then block_target="${line#TARGET }"; continue; fi
      if [[ "$line" == SCOPE* ]]; then block_scope="${line#SCOPE }"; continue; fi
      if [[ "$line" == INHERIT* ]]; then block_inherit="${line#INHERIT }"; continue; fi
      if [[ "$line" == ALLOW* || "$line" == DENY* ]]; then
        rules+=("$(parse_acl_rule_line "$line")")
      fi
    done < "$f"
    if [[ -n "$block_target" ]]; then
      emit_acl_block "$base" "$block_id" "$block_target" "$block_scope" "$block_inherit" "${rules[@]}"
      block_id=$((block_id + 1))
    fi
  done
}

emit_acl_block() {
  local src="$1" block_id="$2" target="$3" scope="$4" inherit="$5"
  shift 5
  target="$(normalize_dn "$target")"
  scope="$(echo "$scope" | tr '[:upper:]' '[:lower:]')"
  inherit="$(echo "$inherit" | tr '[:upper:]' '[:lower:]')"
  local rule idx=0
  for rule in "$@"; do
    IFS='|' read -r effect stype sdn rights attrs <<< "$rule"
    echo "${src}|${block_id}|${idx}|${target}|${scope}|${inherit}|${effect}|${stype}|${sdn}|${rights}|${attrs}"
    idx=$((idx + 1))
  done
}
