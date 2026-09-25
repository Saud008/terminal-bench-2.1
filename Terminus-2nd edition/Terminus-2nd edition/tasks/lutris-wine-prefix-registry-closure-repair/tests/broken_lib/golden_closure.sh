#!/usr/bin/env bash
# Transitive requires closure, cycle detection, runner inheritance.

closure_build() {
  local merged_file="$1"
  local root_slug="$2"
  CLOSURE_ORDER=()
  CLOSURE_CYCLES=()
  CLOSURE_ERRORS=()
  CLOSURE_EDGE_COUNT=0
  CLOSURE_MAX_DEPTH=0
  CLOSURE_RUNNER=""
  CLOSURE_DXVK_VERSION=""

  eval "$(python3 - "${merged_file}" "${root_slug}" <<'PY'
import sys
from collections import defaultdict
from pathlib import Path

merged = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
root = sys.argv[2]

runners: dict[str, str] = {}
pins: dict[str, str] = {}
requires: dict[str, list[str]] = defaultdict(list)
provides: dict[str, str] = {}
exists: set[str] = set()
edge_count = 0
requires_edges: list[tuple[str, str]] = []

for line in merged:
    if not line.strip():
        continue
    parts = line.split("|")
    kind = parts[0]
    if kind == "ENTRY":
        slug, runner, _prefix, pin = parts[1], parts[2], parts[3], parts[4]
        exists.add(slug)
        runners[slug] = runner
        pins[slug] = pin
    elif kind == "REQUIRES":
        slug, dep = parts[1], parts[2]
        requires[slug].append(dep)
        requires_edges.append((slug, dep))
    elif kind == "PROVIDES" and parts[2] == "dxvk_version":
        provides[parts[1]] = parts[3]

errors: list[str] = []
cycles: list[str] = []
order: list[str] = []

def check_missing(slug: str, seen: set[str]) -> None:
    if slug in seen:
        return
    seen.add(slug)
    for dep in requires.get(slug, []):
        if dep not in exists:
            errors.append(f"missing slug {dep}")
        else:
            check_missing(dep, seen)

check_missing(root, set())

if not errors:
    visiting: set[str] = set()
    stack: set[str] = set()

    def dfs(slug: str) -> None:
        visiting.add(slug)
        stack.add(slug)
        for dep in requires.get(slug, []):
            if dep in stack:
                cycles.append(f"{dep},{slug}")
                continue
            if dep not in visiting:
                dfs(dep)
        stack.remove(slug)

    dfs(root)

if not errors and not cycles:
    visited: set[str] = set()

    def topo(slug: str) -> None:
        for dep in sorted(requires.get(slug, [])):
            topo(dep)
        if slug not in visited:
            order.append(slug)
            visited.add(slug)

    topo(root)

runner = ""
for slug in order:
    if runners.get(slug):
        runner = runners[slug]

if not errors and not cycles and not runner:
    errors.append(f"missing runner for {root}")

dxvk = ""
for slug in order:
    if slug in provides:
        dxvk = provides[slug]
        break

max_depth = 0

def depth(slug: str, d: int) -> None:
    global max_depth
    if d > max_depth:
        max_depth = d
    for dep in requires.get(slug, []):
        depth(dep, d + 1)

if not cycles:
    depth(root, 0)

closure_set = set(order)
edge_count = sum(1 for slug, dep in requires_edges if slug in closure_set and dep in closure_set)

def esc(val: str) -> str:
    return val.replace("'", "'\\''")

print(f"CLOSURE_EDGE_COUNT={edge_count}")
print(f"CLOSURE_MAX_DEPTH={max_depth}")
print(f"CLOSURE_RUNNER='{esc(runner)}'")
print(f"CLOSURE_DXVK_VERSION='{esc(dxvk)}'")
print("CLOSURE_ORDER=(" + " ".join(f"'{esc(s)}'" for s in order) + ")")
print("CLOSURE_CYCLES=(" + " ".join(f"'{esc(c)}'" for c in cycles) + ")")
print("CLOSURE_ERRORS=(" + " ".join(f"'{esc(e)}'" for e in errors) + ")")
PY
)"
}
