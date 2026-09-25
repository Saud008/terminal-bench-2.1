"""Independent reference for quadlet parse, order, and render."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/app/tools")
from quadlet_parser import file_meta, list_dropins, unit_name_from_container  # noqa: E402

CLI = "/app/bin/quadlet-resolver"
TOUCH = Path("/app/output/.parser-touch")


def _merge_lists(dst: list[str], src: list[str]) -> None:
    for item in src:
        if item not in dst:
            dst.append(item)


def build_parse_graph(tree: Path) -> dict:
    units: dict[str, dict] = {}
    for base in sorted(tree.rglob("*.container")):
        name = unit_name_from_container(base)
        merged: dict = {"unit": {}, "service": {}, "container": {}}
        fragments = [base] + list_dropins(base)
        for frag in fragments:
            sections = file_meta(frag)["sections"]
            unit = sections.get("Unit", {})
            svc = sections.get("Service", {})
            ctr = sections.get("Container", {})
            for key in ("Wants", "Requires"):
                if key in unit:
                    merged["unit"].setdefault(key, [])
                    vals = unit[key] if isinstance(unit[key], list) else [unit[key]]
                    _merge_lists(merged["unit"][key], vals)
            for key, val in unit.items():
                if key not in ("After", "Wants", "Requires"):
                    merged["unit"][key] = val
            for key, val in svc.items():
                if key == "EnvironmentFile":
                    merged["service"].setdefault(key, [])
                    items = val if isinstance(val, list) else [val]
                    _merge_lists(merged["service"][key], items)
                else:
                    merged["service"][key] = val
            for key, val in ctr.items():
                merged["container"][key] = val
        for frag in fragments:
            sections = file_meta(frag)["sections"]
            unit = sections.get("Unit", {})
            if "After" in unit:
                merged["unit"].setdefault("After", [])
                vals = unit["After"] if isinstance(unit["After"], list) else [unit["After"]]
                _merge_lists(merged["unit"]["After"], vals)
        merged["source"] = str(base.resolve())
        units[name] = merged
    return {"tree": str(tree.resolve()), "units": units}


def build_edges(units: dict[str, dict]) -> dict[str, list[str]]:
    names = sorted(units.keys())
    edges = {n: [] for n in names}
    for unit, meta in units.items():
        u = meta.get("unit", {})
        for key in ("After", "Wants"):
            for dep in u.get(key, []):
                if dep in names and dep != unit:
                    edges[unit].append(dep)
    return edges


def topo_order(units: dict[str, dict]) -> list[str]:
    names = sorted(units.keys())
    edges = build_edges(units)
    indeg = {n: 0 for n in names}
    children = {n: [] for n in names}
    for unit, deps in edges.items():
        for dep in deps:
            children[dep].append(unit)
            indeg[unit] += 1
    queue = sorted([n for n in names if indeg[n] == 0])
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


def render_reference(tree: Path, outdir: Path) -> None:
    parsed = build_parse_graph(tree)
    units = parsed["units"]
    order = topo_order(units)
    outdir.mkdir(parents=True, exist_ok=True)
    for name in order:
        meta = units[name]
        unit = meta.get("unit", {})
        svc = meta.get("service", {})
        ctr = meta.get("container", {})
        lines = ["[Unit]", f"Description={unit.get('Description', name)}"]
        for key in ("After", "Wants", "Requires"):
            vals = unit.get(key, [])
            if vals:
                lines.append(f"{key}={' '.join(vals)}")
        lines.extend(["", "[Service]"])
        for env in svc.get("EnvironmentFile", []):
            lines.append(f"EnvironmentFile={env}")
        lines.append(f"Restart={svc.get('Restart', 'no')}")
        base = name.replace(".service", "")
        image = ctr.get("Image", "localhost/missing:latest")
        lines.append(f"ExecStart=/usr/bin/podman run --name {base} {image}")
        lines.extend(["", "[Install]", "WantedBy=multi-user.target"])
        (outdir / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_unit(path: Path) -> dict[str, dict[str, list[str] | str]]:
    current: str | None = None
    sections: dict[str, dict[str, list[str] | str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if raw.startswith("[") and raw.endswith("]"):
            current = raw[1:-1]
            sections.setdefault(current, {})
            continue
        if current is None or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        if key in {"After", "Wants", "Requires", "EnvironmentFile"}:
            bucket = sections[current].setdefault(key, [])
            assert isinstance(bucket, list)
            for part in val.split():
                if part not in bucket:
                    bucket.append(part)
        else:
            sections[current][key] = val
    return sections


def run_cli_render(tree: Path, outdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "render", "--tree", str(tree), "--out", str(outdir)],
        capture_output=True,
        text=True,
        check=False,
    )


def run_cli_order(tree: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "order", "--tree", str(tree), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
