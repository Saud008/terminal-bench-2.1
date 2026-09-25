#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/common.sh"
source "${LDAPRM_LIB}/dn/normalize.sh"
source "${LDAPRM_LIB}/acl/parse_blocks.sh"
source "${LDAPRM_LIB}/groups/member_closure.sh"

write_staging_snapshot() {
  local ldif="$1" groups="$2" acl_dir="$3" defaults="$4" out="$5"
  local ace_lines closure_lines
  ace_lines="$(parse_acl_directory "$acl_dir")"
  closure_lines="$(expand_group_closure "$groups")"
  python3 - "$ldif" "$groups" "$ace_lines" "$closure_lines" "$defaults" "$out" <<'PY'
import hashlib, json, sys
from pathlib import Path

def normalize_dn(dn):
    parts = []
    for rdn in dn.split(","):
        rdn = rdn.strip()
        if not rdn:
            continue
        if "=" in rdn:
            attr, val = rdn.split("=", 1)
            parts.append(f"{attr.strip().lower()}={val.strip()}")
        else:
            parts.append(rdn.lower())
    return ",".join(parts)

def parse_ldif(path):
    entries = []
    dn, ocs = "", []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("dn:"):
            if dn:
                entries.append({"dn": normalize_dn(dn), "object_classes": sorted(set(ocs))})
            dn = line[3:].strip()
            ocs = []
        elif line.startswith("objectClass:"):
            ocs.append(line.split(":", 1)[1].strip())
    if dn:
        entries.append({"dn": normalize_dn(dn), "object_classes": sorted(set(ocs))})
    entries.sort(key=lambda e: e["dn"])
    return entries

def parse_groups(path):
    graph = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        g, m = line.split("\t", 1)
        g, m = normalize_dn(g.strip()), normalize_dn(m.strip())
        graph.setdefault(g, set()).add(m)
    return graph

ldif, groups, ace_text, closure_text, defaults_path, out = sys.argv[1:7]
entries = parse_ldif(ldif)
graph = parse_groups(groups)
closure = {}
for line in closure_text.splitlines():
    if not line.strip():
        continue
    g, m = line.split("|", 1)
    closure.setdefault(g, set()).add(m)
defaults = json.loads(Path(defaults_path).read_text(encoding="utf-8"))
aces = []
for line in ace_text.splitlines():
    if not line.strip():
        continue
    src, block_id, idx, target, scope, inherit, effect, stype, sdn, rights, attrs = line.split("|", 10)
    aces.append({
        "ace_id": f"{src}:{block_id}:{idx}",
        "target": target,
        "scope": scope,
        "inherit": inherit.lower() in ("yes", "true", "1"),
        "effect": effect,
        "subject_type": stype,
        "subject_dn": sdn,
        "rights": rights.split(","),
        "attrs": [a.strip() for a in attrs.split(",")],
    })
lines = []
for e in entries:
    lines.append(f"entry;{e['dn']};{','.join(e['object_classes'])}")
for a in sorted(aces, key=lambda x: x["ace_id"]):
    lines.append(
        f"ace;{a['ace_id']};{a['target']};{a['scope']};{int(a['inherit'])};"
        f"{a['effect']};{a['subject_type']};{a['subject_dn']};{','.join(a['rights'])};"
        f"{','.join(a['attrs'])}"
    )
for g in sorted(closure):
    for m in sorted(closure[g]):
        lines.append(f"member;{g};{m}")
for oc, spec in sorted(defaults.get("by_objectclass", {}).items()):
    lines.append(f"default;{oc};{','.join(spec.get('rights',[]))};{','.join(spec.get('attrs',['*']))}")
fp = hashlib.sha256("\n".join(lines).encode()).hexdigest()
doc = {
    "schema_version": 1,
    "entries": entries,
    "group_graph": {k: sorted(v) for k, v in graph.items()},
    "group_closure": {k: sorted(v) for k, v in closure.items()},
    "aces": aces,
    "defaults": defaults,
    "staging_fingerprint": fp,
}
Path(out).write_text(json.dumps(doc, indent=2) + "\n")
PY
}
