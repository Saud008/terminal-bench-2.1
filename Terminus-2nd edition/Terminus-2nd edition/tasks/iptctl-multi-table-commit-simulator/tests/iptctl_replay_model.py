"""Independent reference for iptctl simulate exports."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

APP = Path("/app")
SIM_PATH = APP / "tools" / "simulate.py"
KERNEL_ORDER = ["mangle", "nat", "filter"]


def _load_simulate():
    spec = importlib.util.spec_from_file_location("ipt_simulate", SIM_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SIM_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _derived_runtime_cfg(tables: dict[str, Any]) -> dict[str, Any]:
    present = {name for name in tables.keys() if name in {"mangle", "nat", "filter"}}
    mangle_sets = any(
        "-j MARK" in rule.get("spec", "")
        for rule in tables.get("mangle", {}).get("rules", [])
    )
    nat_matches = any(
        "-m mark" in rule.get("spec", "")
        for rule in tables.get("nat", {}).get("rules", [])
    )
    if mangle_sets and nat_matches:
        commit_order = [name for name in KERNEL_ORDER if name in present]
    else:
        commit_order = [name for name in KERNEL_ORDER if name in present]

    zero_policy = True
    drop_rules = True
    for block in tables.values():
        for pol in block.get("policies", []):
            if int(pol.get("packets", 0)) or int(pol.get("bytes", 0)):
                zero_policy = False
        for rule in block.get("rules", []):
            if int(rule.get("packets", 0)) or int(rule.get("bytes", 0)):
                drop_rules = False

    ignore_marks = not (mangle_sets and nat_matches)

    sort_ct = True
    for table_name in ("filter", "mangle"):
        for rule in tables.get(table_name, {}).get("rules", []):
            spec = rule.get("spec", "")
            if "-m conntrack" in spec:
                if "-j CT" in spec and "--notrack" in spec:
                    continue
                sort_ct = False
                break
        if not sort_ct:
            break

    return {
        "commit_order": commit_order,
        "zero_policy_counters": zero_policy,
        "drop_rule_counters": drop_rules,
        "ignore_mangle_marks": ignore_marks,
        "sort_ctstate": sort_ct,
    }


def reference_simulate(restore: Path, seed: str) -> dict[str, Any]:
    mod = _load_simulate()
    tables = mod.parse_restore(restore)
    cfg = _derived_runtime_cfg(tables)
    return mod.simulate(
        restore,
        seed,
        cfg["commit_order"],
        zero_policy_counters=cfg["zero_policy_counters"],
        drop_rule_counters=cfg["drop_rule_counters"],
        ignore_mangle_marks=cfg["ignore_mangle_marks"],
        sort_ctstate=cfg["sort_ctstate"],
    )


def reference_staging(restore: Path) -> dict[str, Any]:
    mod = _load_simulate()
    tables = mod.parse_restore(restore)
    cfg = _derived_runtime_cfg(tables)
    staging = mod.build_staging(restore, cfg)
    staging["binding"]["plan_digest"] = mod.compute_plan_digest(
        restore, staging["phase_config"]
    )
    staging["binding"]["merge_staging_digest"] = mod.merge_staging_digest(staging)
    return staging


def merge_staging_path(staging: Path) -> Path:
    mod = _load_simulate()
    return mod.merge_staging_path(staging)


def reference_export_from_staging(staging_doc: dict[str, Any], seed: str) -> dict[str, Any]:
    mod = _load_simulate()
    return mod.export_from_staging(staging_doc, seed)


def reference_export(restore: Path, seed: str, export: Path) -> int:
    report = reference_simulate(restore, seed)
    export.parent.mkdir(parents=True, exist_ok=True)
    export.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return int(report["exit_code"])
