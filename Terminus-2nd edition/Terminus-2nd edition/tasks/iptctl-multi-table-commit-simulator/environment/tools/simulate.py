#!/usr/bin/env python3
"""Internal restore simulation engine (invoked by /app/lib/)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

POLICY_RE = re.compile(
    r"^:(?P<chain>\S+)\s+(?P<policy>\S+)(?:\s+\[(?P<packets>\d+):(?P<bytes>\d+)\])?\s*$"
)
APPEND_RE = re.compile(
    r"^-A\s+(?P<chain>\S+)\s+(?P<spec>.+?)(?:\s+\[(?P<packets>\d+):(?P<bytes>\d+)\])?\s*$"
)
MARK_SET_RE = re.compile(r"--set-mark\s+(?:0x)?([0-9a-fA-F]+)", re.I)
MARK_MATCH_RE = re.compile(r"--mark\s+(?:0x)?([0-9a-fA-F]+)", re.I)

STAGING_VERSION = 1


def parse_restore(path: Path) -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            current = line[1:].lower()
            tables[current] = {"policies": [], "rules": []}
            continue
        if line == "COMMIT":
            current = None
            continue
        if current is None:
            continue
        if line.startswith(":"):
            m = POLICY_RE.match(line)
            if not m:
                continue
            tables[current]["policies"].append(
                {
                    "table": current,
                    "chain": m.group("chain"),
                    "policy": m.group("policy"),
                    "packets": int(m.group("packets") or 0),
                    "bytes": int(m.group("bytes") or 0),
                }
            )
        elif line.startswith("-A"):
            m = APPEND_RE.match(line)
            if not m:
                continue
            tables[current]["rules"].append(
                {
                    "table": current,
                    "chain": m.group("chain"),
                    "spec": m.group("spec").strip(),
                    "packets": int(m.group("packets") or 0),
                    "bytes": int(m.group("bytes") or 0),
                    "rule_id": len(tables[current]["rules"]),
                }
            )
    return tables


def shuffle_rules(rules: list[dict[str, Any]], seed: str, table: str) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> str:
        rid = item["rule_id"]
        return hashlib.sha256(f"{seed}:{table}:{rid}".encode()).hexdigest()

    return sorted(rules, key=sort_key)


def normalize_mark(token: str) -> str:
    return token.lower().lstrip("0") or "0"


def include_in_conntrack_order(spec: str) -> bool:
    if "-m conntrack" not in spec:
        return False
    if "-j CT" in spec and "--notrack" in spec:
        return False
    return True


def load_runtime_config() -> dict[str, Any]:
    seq_raw = os.environ.get("IPT_CFG_SEQ", "filter,nat,mangle")
    commit_order = [part.strip() for part in seq_raw.split(",") if part.strip()]
    return {
        "commit_order": commit_order,
        "zero_policy_counters": os.environ.get("IPT_CFG_POL", "strip") != "keep",
        "drop_rule_counters": os.environ.get("IPT_CFG_RULE", "strip") != "keep",
        "ignore_mangle_marks": os.environ.get("IPT_CFG_MARK", "isolated") != "linked",
        "sort_ctstate": os.environ.get("IPT_CFG_CT", "lexical") != "chain",
    }


def phase_config_from_runtime(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "commit_order": cfg["commit_order"],
        "policy_mode": "strip" if cfg["zero_policy_counters"] else "keep",
        "rule_counter_mode": "strip" if cfg["drop_rule_counters"] else "keep",
        "mark_mode": "isolated" if cfg["ignore_mangle_marks"] else "linked",
        "ct_mode": "lexical" if cfg["sort_ctstate"] else "chain",
    }


def restore_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_digest_payload(restore_path: Path, phase_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "restore_digest": restore_digest(restore_path),
        "phase_config": phase_config,
    }


def compute_plan_digest(restore_path: Path, phase_config: dict[str, Any]) -> str:
    payload = plan_digest_payload(restore_path, phase_config)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def merge_staging_path(staging_path: Path) -> Path:
    return staging_path.with_suffix(staging_path.suffix + ".merge-staging.json")


def merge_staging_payload(staging: dict[str, Any]) -> dict[str, Any]:
    tables = staging["tables"]
    table_names = sorted(tables.keys())
    rule_counts = {name: len(tables[name]["rules"]) for name in table_names}
    policy_counts = {name: len(tables[name]["policies"]) for name in table_names}
    return {
        "staging_version": STAGING_VERSION,
        "restore_digest": staging["restore_digest"],
        "phase_config": staging["phase_config"],
        "table_names": table_names,
        "rule_counts": rule_counts,
        "policy_counts": policy_counts,
    }


def merge_staging_digest(staging: dict[str, Any]) -> str:
    payload = merge_staging_payload(staging)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_staging(restore_path: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    if not restore_path.is_file():
        raise FileNotFoundError(str(restore_path))
    tables = parse_restore(restore_path)
    phase_config = phase_config_from_runtime(cfg)
    plan_digest = compute_plan_digest(restore_path, phase_config)
    return {
        "staging_version": STAGING_VERSION,
        "restore_path": str(restore_path),
        "restore": restore_path.stem,
        "restore_digest": restore_digest(restore_path),
        "phase_config": phase_config,
        "tables": tables,
        "binding": {
            "plan_digest": plan_digest,
            "merge_staging_digest": merge_staging_digest(
                {
                    "restore_digest": restore_digest(restore_path),
                    "phase_config": phase_config,
                    "tables": tables,
                }
            ),
        },
    }


def simulate_from_tables(
    tables: dict[str, dict[str, Any]],
    seed: str,
    commit_order: list[str],
    *,
    zero_policy_counters: bool,
    drop_rule_counters: bool,
    ignore_mangle_marks: bool,
    sort_ctstate: bool,
    restore_stem: str,
) -> dict[str, Any]:
    shuffled: dict[str, dict[str, Any]] = {}
    for name, data in tables.items():
        shuffled[name] = {
            "policies": list(data["policies"]),
            "rules": shuffle_rules(list(data["rules"]), seed, name),
        }

    present = [t for t in commit_order if t in shuffled]
    marks: set[str] = set()
    rules_out: list[dict[str, Any]] = []
    ct_rules: list[dict[str, Any]] = []
    rule_index = 0

    for table in present:
        data = shuffled[table]
        for rule in data["rules"]:
            spec = rule["spec"]
            packets = 0 if drop_rule_counters else rule["packets"]
            bytes_ = 0 if drop_rule_counters else rule["bytes"]

            if table == "mangle" and "-j MARK" in spec:
                mm = MARK_SET_RE.search(spec)
                if mm:
                    marks.add(normalize_mark(mm.group(1)))

            nat_active = False
            if table == "nat" and "-m mark" in spec:
                mm = MARK_MATCH_RE.search(spec)
                if mm:
                    want = normalize_mark(mm.group(1))
                    visible = marks if not ignore_mangle_marks else set()
                    nat_active = want in visible

            if include_in_conntrack_order(spec) and table in {"filter", "mangle"}:
                ct_rules.append({"table": table, "chain": rule["chain"], "spec": spec})

            rules_out.append(
                {
                    "table": table,
                    "chain": rule["chain"],
                    "index": rule_index,
                    "spec": spec,
                    "packets": packets,
                    "bytes": bytes_,
                    "nat_active": nat_active if table == "nat" else False,
                }
            )
            rule_index += 1

    policies = []
    for table in present:
        for pol in shuffled[table]["policies"]:
            entry = dict(pol)
            if zero_policy_counters:
                entry["packets"] = 0
                entry["bytes"] = 0
            policies.append(entry)
    policies.sort(key=lambda p: (p["table"], p["chain"]))

    if sort_ctstate:
        ct_rules.sort(key=lambda r: r["spec"])

    return {
        "report_version": 1,
        "restore": restore_stem,
        "seed": seed,
        "commit_order": present,
        "policies": policies,
        "rules": rules_out,
        "conntrack_order": ct_rules,
        "exit_code": 0,
    }


def simulate(
    restore_path: Path,
    seed: str,
    commit_order: list[str],
    *,
    zero_policy_counters: bool,
    drop_rule_counters: bool,
    ignore_mangle_marks: bool,
    sort_ctstate: bool,
) -> dict[str, Any]:
    tables = parse_restore(restore_path)
    return simulate_from_tables(
        tables,
        seed,
        commit_order,
        zero_policy_counters=zero_policy_counters,
        drop_rule_counters=drop_rule_counters,
        ignore_mangle_marks=ignore_mangle_marks,
        sort_ctstate=sort_ctstate,
        restore_stem=restore_path.stem,
    )


def export_from_staging(staging: dict[str, Any], seed: str) -> dict[str, Any]:
    phase = staging["phase_config"]
    cfg = {
        "commit_order": phase["commit_order"],
        "zero_policy_counters": phase["policy_mode"] != "keep",
        "drop_rule_counters": phase["rule_counter_mode"] != "keep",
        "ignore_mangle_marks": phase["mark_mode"] != "linked",
        "sort_ctstate": phase["ct_mode"] != "chain",
    }
    return simulate_from_tables(
        staging["tables"],
        seed,
        cfg["commit_order"],
        zero_policy_counters=cfg["zero_policy_counters"],
        drop_rule_counters=cfg["drop_rule_counters"],
        ignore_mangle_marks=cfg["ignore_mangle_marks"],
        sort_ctstate=cfg["sort_ctstate"],
        restore_stem=staging["restore"],
    )


def missing_restore_report(restore: Path, seed: str) -> dict[str, Any]:
    return {
        "report_version": 1,
        "restore": restore.stem,
        "seed": seed,
        "commit_order": [],
        "policies": [],
        "rules": [],
        "conntrack_order": [],
        "exit_code": 2,
    }


def cmd_direct(restore: Path, seed: str, export: Path) -> int:
    if not restore.is_file():
        report = missing_restore_report(restore, seed)
        export.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 2
    cfg = load_runtime_config()
    report = simulate(
        restore,
        seed,
        cfg["commit_order"],
        zero_policy_counters=cfg["zero_policy_counters"],
        drop_rule_counters=cfg["drop_rule_counters"],
        ignore_mangle_marks=cfg["ignore_mangle_marks"],
        sort_ctstate=cfg["sort_ctstate"],
    )
    export.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return int(report["exit_code"])


def cmd_export(staging_path: Path, seed: str, export: Path) -> int:
    if not staging_path.is_file():
        return 4
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    report = export_from_staging(staging, seed)
    export.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return int(report["exit_code"])


def main() -> int:
    if len(sys.argv) < 2:
        return 2
    if sys.argv[1] == "export":
        if len(sys.argv) != 5:
            return 2
        return cmd_export(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    if len(sys.argv) != 4:
        return 2
    return cmd_direct(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))


if __name__ == "__main__":
    raise SystemExit(main())
