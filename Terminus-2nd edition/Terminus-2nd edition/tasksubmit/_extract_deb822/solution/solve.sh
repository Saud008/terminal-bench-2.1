# Oracle solve — task identity bash-deb822-apt-pin-priority-explainer token 30c69512
#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/lib/pq7m/w01/f010.sh <<'DEBPOL_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

read_deb822_stanzas() {
  local path="$1"
  python3 - <<'PY' "$path"
import json, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
stanzas, cur, last_key = [], {}, None
for line in text.splitlines():
    if not line.strip():
        if cur:
            stanzas.append(cur)
            cur, last_key = {}, None
        continue
    if line.startswith(" "):
        if last_key:
            cur[last_key] = (cur.get(last_key, "") + " " + line.strip()).strip()
        continue
    if ":" in line:
        k, v = line.split(":", 1)
        last_key = k.strip()
        cur[last_key] = v.strip()
if cur:
    stanzas.append(cur)
print(json.dumps(stanzas))
PY
}
DEBPOL_ORACLE_EOF
chmod +x /app/lib/pq7m/w01/f010.sh
bash -n /app/lib/pq7m/w01/f010.sh

cat > /app/lib/pq7m/w02/f011.sh <<'DEBPOL_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

rank_origins() {
  local origins_json="$1"
  echo "$origins_json" | jq -c 'sort_by(.["Default-Pin"] // "500" | tonumber) | reverse'
}
DEBPOL_ORACLE_EOF
chmod +x /app/lib/pq7m/w02/f011.sh
bash -n /app/lib/pq7m/w02/f011.sh

cat > /app/lib/pq7m/w03/f012.sh <<'DEBPOL_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

effective_pin() {
  local prefs_json="$1"
  local pkg="$2"
  local ver="$3"
  local best=0
  while IFS= read -r pref; do
    [[ -z "$pref" ]] && continue
    pin_pkg=$(echo "$pref" | jq -r '.Package // "*"')
    [[ "$pin_pkg" != "*" && "$pin_pkg" != "$pkg" ]] && continue
    pin_field=$(echo "$pref" | jq -r '.Pin // ""')
    prio=$(echo "$pref" | jq -r '.["Pin-Priority"] // "0"')
    if [[ "$pin_field" == version* ]]; then
      pat="${pin_field#version }"
      match=$(python3 - <<'PY' "$ver" "$pat"
import fnmatch, sys
v = sys.argv[1].split("-")[0]
if ":" in v:
    v = v.split(":", 1)[1]
print("ok" if fnmatch.fnmatch(v, sys.argv[2]) else "no")
PY
)
      [[ "$match" == "ok" ]] || continue
    fi
    if (( prio > best )); then
      best=$prio
    fi
  done < <(echo "$prefs_json" | jq -c '.[]')
  echo "$best"
}
DEBPOL_ORACLE_EOF
chmod +x /app/lib/pq7m/w03/f012.sh
bash -n /app/lib/pq7m/w03/f012.sh

cat > /app/lib/pq7m/w03/f013.sh <<'DEBPOL_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

dpkg_version_newer() {
  local a="$1"
  local b="$2"
  python3 - <<'PY' "$a" "$b"
import sys

def parse(v):
    epoch = 0
    if ":" in v:
        e, rest = v.split(":", 1)
        epoch = int(e)
        v = rest
    if "-" in v:
        upstream, deb = v.rsplit("-", 1)
    else:
        upstream, deb = v, "0"
    return (epoch, upstream, deb)

def cmp_segment(x, y):
    if x == y:
        return 0
    for a, b in zip(x, y):
        if a != b:
            return (a > b) - (a < b)
    return (len(x) < len(y)) - (len(x) > len(y))

def cmp_up(a, b):
    aa = a.replace("~", "\x00")
    bb = b.replace("~", "\x00")
    pa, pb = aa.split("."), bb.split(".")
    for x, y in zip(pa, pb):
        if x == y:
            continue
        if x.isdigit() and y.isdigit():
            return (int(x) > int(y)) - (int(x) < int(y))
        return cmp_segment(x, y)
    return (len(pa) > len(pb)) - (len(pa) < len(pb))

def cmp_ver(a, b):
    ea, ua, da = parse(a)
    eb, ub, db = parse(b)
    if ea != eb:
        return ea - eb
    c = cmp_up(ua, ub)
    if c:
        return c
    return cmp_up(da, db)

sys.exit(0 if cmp_ver(sys.argv[1], sys.argv[2]) > 0 else 1)
PY
}
DEBPOL_ORACLE_EOF
chmod +x /app/lib/pq7m/w03/f013.sh
bash -n /app/lib/pq7m/w03/f013.sh

cat > /app/lib/pq7m/w04/f014.sh <<'DEBPOL_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

cpu_arch_allowed() {
  local cand_arch="$1"
  local target="$2"
  [[ -n "$cand_arch" ]] || return 1
  [[ "$cand_arch" == "all" || "$cand_arch" == "$target" ]]
}
DEBPOL_ORACLE_EOF
chmod +x /app/lib/pq7m/w04/f014.sh
bash -n /app/lib/pq7m/w04/f014.sh

cat > /app/lib/pq7m/w04/f015.sh <<'DEBPOL_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

graph_digest() {
  local body_json="$1"
  python3 - <<'PY' "$body_json"
import hashlib, json, sys
body = json.loads(sys.argv[1])
slim = {
    "run_id": body["run_id"],
    "origin_fingerprint": body.get("origin_fingerprint", ""),
    "packages": [
        {"name": p["package"], "version": p["version"], "origin_id": p.get("origin_id", "")}
        for p in body["package_rows"]
    ],
}
print(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
PY
}
DEBPOL_ORACLE_EOF
chmod +x /app/lib/pq7m/w04/f015.sh
bash -n /app/lib/pq7m/w04/f015.sh

python3 - <<'PATCH'
from pathlib import Path
p = Path("/app/lib/pq7m/w06/f017.sh")
text = p.read_text(encoding="utf-8")
old = """origin_fp=$(echo "$ranked" | jq -c '[.[].["X-Source-Id"]] | join("|")' | sha256sum | awk '{print $1}')"""
new = """origin_fp=$(echo "$ranked" | jq -r 'map(.["X-Source-Id"]) | join("|")' | sha256sum | awk '{print $1}')"""
if old not in text:
    raise SystemExit("f017 origin_fp patch anchor missing")
text = text.replace(old, new)
old = """  '{run_id, scenario, target_arch: $arch, origins, preferences, package_rows, queries, origin_fingerprint: $origin_fingerprint}')"""
new = """  '{run_id: $run_id, scenario: $scenario, target_arch: $arch, origins: $origins, preferences: $preferences, package_rows: $package_rows, queries: $queries, origin_fingerprint: $origin_fingerprint}')"""
if old not in text:
    raise SystemExit("f017 body jq patch anchor missing")
p.write_text(text.replace(old, new), encoding="utf-8")
PATCH
chmod +x /app/lib/pq7m/w06/f017.sh
bash -n /app/lib/pq7m/w06/f017.sh

python3 - <<'PATCH'
from pathlib import Path
p = Path("/app/lib/pq7m/w05/f016.sh")
text = p.read_text(encoding="utf-8")
old = """    elif (( prio == best_prio )) && [[ -n "$best" ]]; then
      # Baseline keeps first candidate on priority tie.
      :
    fi"""
new = """    elif (( prio == best_prio )) && [[ -n "$best" ]]; then
      if dpkg_version_newer "$ver" "$best"; then
        best="$ver"
        best_origin="$oid"
      fi
    fi"""
if old not in text:
    raise SystemExit("f016 tie-break patch anchor missing")
p.write_text(text.replace(old, new), encoding="utf-8")
PATCH
chmod +x /app/lib/pq7m/w05/f016.sh
bash -n /app/lib/pq7m/w05/f016.sh

bash /app/scripts/rebuild-debpol.sh
bash /app/scripts/reset-state.sh

/app/bin/debpol build-policy --scenario vendor-fetch-dual --run-id oracle-smoke >/dev/null
test -s /app/state/deb822-policy-graph.json
/app/bin/debpol candidate-report --run-id oracle-smoke --output /app/output/oracle-smoke.json >/dev/null
test -s /app/output/oracle-smoke.json
