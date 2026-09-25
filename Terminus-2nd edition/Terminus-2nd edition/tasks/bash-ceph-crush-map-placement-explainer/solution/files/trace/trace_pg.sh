#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/crpe91/bucket/traverse.sh"
source "${APP_ROOT}/internal/crpe91/osd/filter_status.sh"
source "${APP_ROOT}/internal/crpe91/weight/normalize.sh"
source "${APP_ROOT}/internal/crpe91/rule/apply_steps.sh"

trace_pg_placement() {
  local loaded="$1"
  local pg_num="$2"
  python3 - <<'PY' "$loaded" "$pg_num"
import hashlib, json, sys

def crush_hash(pool_id, pg_num, item_id, retry):
    s = f"{pool_id}.{pg_num}.{item_id}.{retry}"
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)

def eff(o):
    return float(o["weight"]) * float(o.get("reweight", 1.0))

def eligible(o):
    return o.get("status") == "up" and o.get("in", True)

def normalize_weights(items):
    total = sum(w for _, w in items)
    if total <= 0:
        return []
    scale = 65536.0 / total
    return [(i, int(w * scale)) for i, w in items]

def weighted_pick(items, h):
    total = sum(w for _, w in items)
    slot = h % total
    acc = 0
    for item_id, wt in items:
        acc += wt
        if slot < acc:
            return item_id
    return items[-1][0]

loaded = json.loads(open(sys.argv[1]).read())
pg_num = int(sys.argv[2])
pool = loaded["pool"]
buckets = loaded["crush"]["buckets"]
rules = loaded["crush"]["rules"]
bmap = {int(b["id"]): b for b in buckets}
bname = {b["name"]: b for b in buckets}
osds = {int(o["id"]): o for o in loaded["osd"]["osds"]}
rule = next(r for r in rules if int(r["id"]) == int(pool["crush_rule"]))

def collect_hosts(root):
    out = []
    def walk(bid):
        b = bmap[bid]
        if b["type"] == "host":
            out.append(b)
            return
        for child in b.get("children", []):
            walk(int(child["id"]))
    walk(int(root["id"]))
    out.sort(key=lambda h: h["name"])
    return out

def host_osds(host):
    rows = []
    for child in host.get("children", []):
        oid = int(child["id"])
        if oid in osds:
            rows.append(osds[oid])
    rows.sort(key=lambda o: int(o["id"]))
    return rows

acting = []
steps = []
retry = 0
cursor = None
want = int(pool["size"])
for st in rule["steps"]:
    if st["op"] == "take":
        cursor = bname[str(st["arg"])]
        steps.append({"op": "take", "bucket": cursor["name"], "bucket_id": cursor["id"]})
    elif st["op"] == "chooseleaf":
        target = int(st["arg"]["num"])
        hosts = collect_hosts(cursor)
        excluded = set()
        for host in hosts:
            for osd in host_osds(host):
                if not eligible(osd):
                    excluded.add(int(osd["id"]))
        while len(acting) < min(target, want):
            placed = False
            for host in hosts:
                if len(acting) >= min(target, want):
                    break
                cands = []
                host_ex = []
                for osd in host_osds(host):
                    oid = int(osd["id"])
                    if not eligible(osd):
                        host_ex.append(oid)
                        continue
                    if oid in acting:
                        continue
                    cands.append((oid, eff(osd)))
                if not cands:
                    continue
                norm = normalize_weights(cands)
                pick = weighted_pick(norm, crush_hash(int(pool["id"]), pg_num, int(host["id"]), retry))
                acting.append(pick)
                steps.append({
                    "op": "chooseleaf",
                    "host": host["name"],
                    "selected_osd": pick,
                    "excluded_osds": sorted(set(host_ex) | excluded),
                    "retry": retry,
                })
                retry += 1
                placed = True
                break
            if not placed:
                break
    elif st["op"] == "emit":
        steps.append({"op": "emit", "acting_set": list(acting)})

acting = acting[:want]
pool_id = int(pool["id"])
print(json.dumps({
    "pg_id": f"{pool_id}.{pg_num:x}",
    "pool_id": pool_id,
    "pg_num": pg_num,
    "primary_osd": acting[0] if acting else -1,
    "acting_set": acting,
    "steps": steps,
}))
PY
}
