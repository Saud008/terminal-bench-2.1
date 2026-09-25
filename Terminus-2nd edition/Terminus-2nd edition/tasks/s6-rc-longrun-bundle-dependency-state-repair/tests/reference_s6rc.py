"""Independent reference for s6-rc bundle ingest, DAG, ready, apply, export.

Parser lives here (protected verifier), not under agent-writable /app/tools.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

CLI = "/app/bin/s6-bundle-resolver"
TOUCH = Path("/app/output/.parser-touch")
STATE = Path("/app/state")


def parse_bundle(path: Path) -> dict:
    """Parse one .bundle file using the public grammar in bundle-format.md."""
    bundle_name = ""
    services: dict[str, str] = {}
    hard_deps: list[list[str]] = []
    soft_deps: list[list[str]] = []
    longruns: list[str] = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        head = parts[0]
        if head == "bundle" and len(parts) >= 2:
            bundle_name = parts[1]
        elif head == "service" and len(parts) >= 3:
            services[parts[1]] = parts[2]
        elif head == "dep" and len(parts) >= 4 and parts[2] == "hard":
            hard_deps.append([parts[1], parts[3]])
        elif head == "dep" and len(parts) >= 4 and parts[2] == "soft":
            # dep CHILD soft PARENT → [CHILD, PARENT]
            soft_deps.append([parts[1], parts[3]])
        elif (
            head == "soft"
            and len(parts) >= 5
            and parts[1] == "dep"
            and parts[3] == "soft"
        ):
            # soft dep CHILD soft PARENT → [CHILD, PARENT]
            soft_deps.append([parts[2], parts[4]])
        elif head == "longrun" and len(parts) >= 2:
            longruns.append(parts[1])

    if not bundle_name:
        bundle_name = path.stem

    return {
        "name": bundle_name,
        "source": str(path.resolve()),
        "services": [{"name": n, "type": t} for n, t in sorted(services.items())],
        "hard_deps": hard_deps,
        "soft_deps": soft_deps,
        "longruns": sorted(set(longruns)),
    }


def ingest_tree(tree: Path, touch: Path | None = None) -> dict:
    bundles: dict[str, dict] = {}
    for path in sorted(tree.rglob("*.bundle")):
        meta = parse_bundle(path)
        bundles[meta["name"]] = meta
        if touch is not None:
            with touch.open("a", encoding="utf-8") as fh:
                fh.write(f"{path.resolve()}\n")
    return {"tree": str(tree.resolve()), "bundles": bundles}


def build_ingest(tree: Path) -> dict:
    return ingest_tree(tree, None)


def hard_edges(bundle: dict) -> dict[str, list[str]]:
    names = [s["name"] for s in bundle["services"]]
    edges = {n: [] for n in names}
    for child, parent in bundle.get("hard_deps", []):
        if child in names and parent in names and child != parent:
            edges[child].append(parent)
    for unit in edges:
        edges[unit].sort()
    return edges


def find_cycle(bundle: dict) -> list[str] | None:
    names = sorted(s["name"] for s in bundle["services"])
    edges = hard_edges(bundle)
    state: dict[str, int] = {}
    stack: list[str] = []
    cycle: list[str] = []

    def dfs(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dep in edges.get(node, []):
            if dep not in state:
                dfs(dep)
            elif state[dep] == 1:
                i = stack.index(dep)
                cycle.extend(stack[i:] + [dep])
                return
        state[node] = 2
        stack.pop()

    for node in names:
        if node not in state:
            dfs(node)
        if cycle:
            return cycle
    return None


def topo_plan(bundle: dict) -> list[str]:
    names = sorted(s["name"] for s in bundle["services"])
    edges = hard_edges(bundle)
    indeg = {n: 0 for n in names}
    children = {n: [] for n in names}
    for unit, deps in edges.items():
        for dep in deps:
            children[dep].append(unit)
            indeg[unit] += 1
    queue = sorted(n for n in names if indeg[n] == 0)
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in sorted(children.get(node, [])):
            indeg[child] -= 1
            if indeg[child] == 0:
                queue.append(child)
                queue.sort()
    return order


def all_edges(bundle: dict) -> list[dict]:
    edges: list[dict] = []
    for child, parent in bundle.get("hard_deps", []):
        edges.append({"from": child, "to": parent, "kind": "hard"})
    for child, parent in bundle.get("soft_deps", []):
        edges.append({"from": child, "to": parent, "kind": "soft"})
    edges.sort(key=lambda e: (e["from"], e["to"], e["kind"]))
    return edges


def ready_map(bundle: dict, rc: dict[str, str]) -> dict[str, dict]:
    hard_parents: dict[str, list[str]] = {n: [] for n in bundle.get("longruns", [])}
    for child, parent in bundle.get("hard_deps", []):
        if child in hard_parents:
            hard_parents[child].append(parent)
    for key in hard_parents:
        hard_parents[key] = sorted(set(hard_parents[key]))
    longruns: dict[str, dict] = {}
    for name in sorted(bundle.get("longruns", [])):
        blocked = [p for p in hard_parents.get(name, []) if rc.get(p, "down") != "up"]
        longruns[name] = {"ready": len(blocked) == 0, "blocked_by": blocked}
    return longruns


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([CLI, *args], capture_output=True, text=True, check=False)


def run_ingest(tree: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return run_cli(["ingest", "--tree", str(tree), "--out", str(out)])


def run_validate(tree: Path, bundle: str) -> subprocess.CompletedProcess[str]:
    return run_cli(["validate", "--tree", str(tree), "--bundle", bundle])


def run_plan(tree: Path, bundle: str, out: Path) -> subprocess.CompletedProcess[str]:
    return run_cli(["plan", "--tree", str(tree), "--bundle", bundle, "--out", str(out)])


def run_ready(tree: Path, bundle: str, state_dir: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return run_cli(
        [
            "ready",
            "--tree",
            str(tree),
            "--bundle",
            bundle,
            "--state-dir",
            str(state_dir),
            "--out",
            str(out),
        ]
    )


def run_apply(tree: Path, bundle: str, bundle_id: str, state_dir: Path) -> subprocess.CompletedProcess[str]:
    return run_cli(
        [
            "apply",
            "--tree",
            str(tree),
            "--bundle",
            bundle,
            "--bundle-id",
            bundle_id,
            "--state-dir",
            str(state_dir),
        ]
    )


def run_export(tree: Path, bundle: str, out: Path) -> subprocess.CompletedProcess[str]:
    return run_cli(["export", "--tree", str(tree), "--bundle", bundle, "--out", str(out)])


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_rc(state_dir: Path, mapping: dict[str, str]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "services.json").write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
