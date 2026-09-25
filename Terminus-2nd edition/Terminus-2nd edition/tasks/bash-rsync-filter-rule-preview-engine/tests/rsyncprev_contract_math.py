"""Independent rsync filter preview contract math."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any


def _parse_rules(rows: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, raw in enumerate(rows):
        raw = str(raw).strip()
        if not raw or raw.startswith("#"):
            continue
        out.append({"token": raw[0], "pattern": raw[1:].strip(), "index": i})
    return out


def _matches(path: str, pattern: str) -> bool:
    anchored = False
    if pattern.startswith("/"):
        anchored = True
        pattern = pattern[1:]
    if pattern.endswith("/**"):
        base = pattern[:-3]
        if path == base or path.startswith(base + "/"):
            return True
    if anchored:
        return fnmatch.fnmatch(path, pattern)
    leaf = path.split("/")[-1]
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(leaf, pattern)


def _cascaded_rules(path: str, root_rules: list[str], cascade_overlays: dict[str, list[str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    dirs: list[str] = []
    acc: list[str] = []
    for part in path.split("/")[:-1]:
        acc.append(part)
        dirs.append("/".join(acc))

    merged = list(root_rules)
    ledger = [{"directory": "/", "added_rules": len(root_rules)}]
    for d in dirs:
        rows = cascade_overlays.get(d, [])
        if rows:
            merged.extend(rows)
            ledger.append({"directory": d, "added_rules": len(rows)})
    return _parse_rules(merged), ledger, len(ledger)


def _first_match(path: str, parsed: list[dict[str, Any]]) -> dict[str, Any]:
    for row in parsed:
        if _matches(path, row["pattern"]):
            token = row["token"]
            transfer = "exclude" if token in ("-", "P", "R") else "include"
            return {"transfer": transfer, "token": token, "matched_rule_index": row["index"]}
    return {"transfer": "include", "token": "+", "matched_rule_index": -1}


def _delete_risk(
    path: str,
    transfer: str,
    parsed: list[dict[str, Any]],
    sender: set[str],
    receiver: set[str],
) -> str:
    if path not in receiver:
        return "none"
    if any(row["token"] == "P" and _matches(path, row["pattern"]) for row in parsed):
        return "protected"
    receiver_only = path not in sender
    if receiver_only and any(row["token"] == "R" and _matches(path, row["pattern"]) for row in parsed):
        return "candidate"
    if receiver_only and transfer == "exclude":
        return "candidate"
    return "none"


def reference_preview(manifest_path: Path, run_id: str) -> dict[str, Any]:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    sender = set(m["sender_paths"])
    receiver = set(m["receiver_paths"])
    all_paths = sorted(sender | receiver)
    verdicts = []
    rule_cascade = []
    for path in all_paths:
        parsed, ledger, depth = _cascaded_rules(path, m["root_rules"], m["cascade_overlays"])
        match = _first_match(path, parsed)
        transfer = match["transfer"]
        if path not in sender:
            transfer = "exclude"
        prune = "." not in path.split("/")[-1] and transfer == "exclude"
        verdicts.append(
            {
                "path": path,
                "transfer": transfer,
                "delete_risk": _delete_risk(path, transfer, parsed, sender, receiver),
                "cascade_depth": depth,
                "matched_rule_index": match["matched_rule_index"],
                "prune": prune,
            }
        )
        rule_cascade.append({"path": path, "cascade": ledger})

    summary = {
        "include_count": sum(1 for row in verdicts if row["transfer"] == "include"),
        "exclude_count": sum(1 for row in verdicts if row["transfer"] == "exclude"),
        "candidate_delete_count": sum(1 for row in verdicts if row["delete_risk"] == "candidate"),
        "protected_delete_count": sum(1 for row in verdicts if row["delete_risk"] == "protected"),
    }
    return {"run_id": run_id, "tree": m["tree"], "path_verdicts": verdicts, "rule_cascade": rule_cascade, "summary": summary}
