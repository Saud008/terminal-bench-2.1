#!/usr/bin/env bash

s2_compute_mount_order() {
  local rootfs="$1"
  python3 - "$rootfs/mounts.json" <<'PY'
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8"))
mounts = doc["mounts"]
by_id = {m["id"]: m for m in mounts}
ids = [m["id"] for m in mounts]
in_deg = {i: 0 for i in ids}
edges: set[tuple[str, str]] = set()

def add_edge(src: str, dst: str) -> None:
    if src == dst or src not in by_id or dst not in by_id:
        return
    if (src, dst) in edges:
        return
    edges.add((src, dst))
    in_deg[dst] += 1

targets = {m["target"]: m["id"] for m in mounts}
for m in mounts:
    for dep in m.get("after") or []:
        add_edge(dep, m["id"])
    t = m["target"]
    if t != "/":
        parent = t.rsplit("/", 1)[0] or "/"
        if parent in targets and parent != t:
            add_edge(targets[parent], m["id"])
    if m.get("kind") == "bind":
        for vm in mounts:
            if vm.get("id") in ("proc", "sysfs"):
                add_edge(vm["id"], m["id"])
    if m["id"] == "devbind":
        add_edge("proc", m["id"])
    if m["id"] == "devpts":
        parent = m["target"].rsplit("/", 1)[0] or "/"
        if parent in targets:
            add_edge(targets[parent], m["id"])

queue = [i for i in ids if in_deg[i] == 0]
result: list[str] = []
while queue:
    queue.sort(key=lambda i: (0 if by_id[i].get("kind") == "virtual" else 1, i))
    pick = queue.pop(0)
    result.append(pick)
    for src, dst in list(edges):
        if src == pick:
            in_deg[dst] -= 1
            if in_deg[dst] == 0:
                queue.append(dst)
if len(result) != len(ids):
    raise SystemExit("mount cycle detected")
for mid in result:
    print(mid)
PY
}
