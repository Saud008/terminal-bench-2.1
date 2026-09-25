"""Independent kconfig attestor contract math for pytest."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/app/tools")
from kcfg_primitives import manifest_digest as _manifest_digest
from kcfg_primitives import stage_digest as _stage_digest


def parse_kconfig(path: Path) -> dict[str, str]:
    symbols: dict[str, str] = {}
    unset = re.compile(r"^#\s*(CONFIG_\w+)\s+is not set\s*$")
    assign = re.compile(r"^(CONFIG_\w+)=(y|m|n)$")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        m = unset.match(line)
        if m:
            symbols[m.group(1)] = "n"
            continue
        m = assign.match(line)
        if m:
            symbols[m.group(1)] = m.group(2)
    return symbols


def fragment_order(frag_dir: Path) -> list[str]:
    return sorted(p.name for p in frag_dir.glob("*.fragment"))


def merge_layers(defconfig: Path, frag_dir: Path) -> dict[str, str]:
    merged: dict[str, str] = {}
    merged.update(parse_kconfig(defconfig))
    for frag in fragment_order(frag_dir):
        merged.update(parse_kconfig(frag_dir / frag))
    return merged


def apply_deps(symbols: dict[str, str], deps: dict[str, Any]) -> dict[str, str]:
    out = dict(symbols)
    requires = deps.get("requires", {})
    implies = deps.get("implies", {})
    selects = deps.get("selects", {})

    def enabled(val: str | None) -> bool:
        return val in ("y", "m")

    changed = True
    while changed:
        changed = False
        for sym, val in list(out.items()):
            if not enabled(val):
                continue
            for req in requires.get(sym, []):
                if out.get(req) != "y":
                    out[req] = "y"
                    changed = True
            for child in implies.get(sym, []):
                if out.get(child) != "y":
                    out[child] = "y"
                    changed = True
        for parent, children in selects.items():
            if out.get(parent) == "y":
                for child in children:
                    if out.get(child) != "y":
                        out[child] = "y"
                        changed = True
    return dict(sorted(out.items()))


def scan_policy(symbols: dict[str, str], policy: dict[str, Any]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for sym in policy.get("forbidden_if_set", []):
        if symbols.get(sym) in ("y", "m"):
            violations.append(
                {"symbol": sym, "code": "forbidden_set", "detail": "symbol must not be enabled"}
            )
    for sym in policy.get("required_n", []):
        if symbols.get(sym) not in (None, "n"):
            violations.append(
                {"symbol": sym, "code": "required_n", "detail": "symbol must be disabled"}
            )
    for sym in policy.get("max_modular", []):
        if symbols.get(sym) == "y":
            violations.append(
                {"symbol": sym, "code": "max_modular", "detail": "symbol must be modular or disabled"}
            )
    return sorted(violations, key=lambda v: v["symbol"])


def stage_digest(run_id: str, bundle: str, frag_order: list[str], symbols: dict[str, str]) -> str:
    return _stage_digest(run_id, bundle, frag_order, symbols)


def manifest_digest(rows: list[dict[str, str]]) -> str:
    return _manifest_digest(rows)


def contract_stage(bundle_dir: Path, run_id: str) -> dict[str, Any]:
    deps = json.loads((bundle_dir / "deps.json").read_text(encoding="utf-8"))
    policy = json.loads((bundle_dir / "policy.json").read_text(encoding="utf-8"))
    frag_dir = bundle_dir / "fragments"
    order = fragment_order(frag_dir)
    raw = merge_layers(bundle_dir / "defconfig", frag_dir)
    after = apply_deps(raw, deps)
    violations = scan_policy(after, policy)
    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))["name"]
    digest = stage_digest(run_id, bundle, order, after)
    return {
        "run_id": run_id,
        "bundle": bundle,
        "fragment_order": order,
        "raw_merged": raw,
        "after_deps": after,
        "policy_violations": violations,
        "deps": deps,
        "policy": policy,
        "stage_digest": digest,
    }


def contract_manifest(bundle_dir: Path, run_id: str) -> dict[str, Any]:
    stage = contract_stage(bundle_dir, run_id)
    rows = [
        {"name": k, "value": v, "source_layer": "contract"}
        for k, v in sorted(stage["after_deps"].items())
    ]
    digest = manifest_digest(rows)
    return {
        "run_id": run_id,
        "symbols": rows,
        "policy_violations": stage["policy_violations"],
        "totals": {"symbols": len(rows), "violations": len(stage["policy_violations"])},
        "manifest_digest": digest,
    }


def symbol_map(manifest: dict[str, Any]) -> dict[str, str]:
    return {row["name"]: row["value"] for row in manifest["symbols"]}
