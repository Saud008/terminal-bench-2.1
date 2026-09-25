"""Independent reference for tmpfiles-replay apply and generate."""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
from copy import deepcopy
from pathlib import Path

APP = Path("/app")
WORK = APP / "work"
TREE = WORK / "tree"
FIXTURES = APP / "fixtures" / "scenarios"


def parse_age(token: str) -> int | None:
    if token in ("-", ""):
        return None
    if token.isdigit():
        return int(token)
    num = int(token[:-1])
    unit = token[-1]
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    return num * mult


def parse_rules(rules_file: Path) -> list[dict]:
    rules: list[dict] = []
    for raw in rules_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        typ = parts[0]
        path = parts[1]
        if typ in ("d", "z", "o"):
            rules.append(
                {
                    "type": typ,
                    "path": path,
                    "mode": parts[2] if len(parts) > 2 else "-",
                    "user": parts[3] if len(parts) > 3 else "-",
                    "group": parts[4] if len(parts) > 4 else "-",
                    "age": parse_age(parts[5]) if len(parts) > 5 else None,
                }
            )
        elif typ in ("r", "r!"):
            row: dict = {
                "type": "r!",
                "path": path,
                "age": parse_age(parts[2]) if len(parts) > 2 else None,
                "exclude_depth": 0,
            }
            for extra in parts[3:]:
                if extra.startswith("e") and extra[1:].isdigit():
                    row["exclude_depth"] = int(extra[1:])
            rules.append(row)
        elif typ == "x":
            rules.append({"type": "x", "path": path})
    return rules


def globstar_match(pattern: str, candidate: str) -> bool:
    if "**" in pattern:
        regex = "^" + re.escape(pattern).replace("\\*\\*", ".*").replace("\\*", "[^/]*") + "$"
        return re.match(regex, candidate) is not None
    return fnmatch.fnmatch(candidate, pattern)


def anchor_dir(glob_pattern: str) -> str:
    before_star = glob_pattern.split("*", 1)[0]
    return os.path.normpath(before_star.rstrip("/")) or "/"


def relative_depth(anchor: str, candidate: str) -> int:
    anchor = anchor.rstrip("/") or "/"
    cand = candidate.rstrip("/")
    if not cand.startswith(anchor):
        return 0
    rest = cand[len(anchor) :].lstrip("/")
    if not rest:
        return 0
    return len(rest.split("/"))


def age_eligible(meta: dict, age_sec: int, now: int) -> bool:
    stamp = max(int(meta.get("atime", 0)), int(meta.get("btime", 0)))
    return now - stamp >= age_sec


def is_excluded(candidate: str, exclude_depth: int, x_rules: list[dict], rule_glob: str) -> bool:
    depth = relative_depth(anchor_dir(rule_glob), candidate)
    for row in x_rules:
        if globstar_match(row["path"], candidate) and depth <= exclude_depth:
            return True
    return False


def pending_removals_under(prefix: str, rules: list[dict], tree: dict, now: int, x_rules: list[dict]) -> list[str]:
    pending: list[str] = []
    prefix = prefix.rstrip("/") or "/"
    for rule in rules:
        if rule["type"] != "r!":
            continue
        age_sec = rule.get("age") or 0
        glob_pat = rule["path"]
        for path, meta in tree["paths"].items():
            if not path.startswith(prefix + "/") and path != prefix:
                continue
            if not globstar_match(glob_pat, path):
                continue
            if is_excluded(path, rule.get("exclude_depth", 0), x_rules, glob_pat):
                continue
            if age_eligible(meta, age_sec, now):
                pending.append(path)
    return pending


def apply_recreate(path: str, mode: str, user: str, group: str, tree: dict) -> None:
    kind = "d" if mode.startswith("0") and len(mode) == 4 else "f"
    tree["paths"][path] = {
        "kind": kind,
        "mode": mode,
        "user": user,
        "group": group,
        "atime": 0,
        "btime": 0,
        "mtime": 0,
    }


def apply_ownership(path: str, mode: str, user: str, group: str, tree: dict) -> bool:
    if path not in tree["paths"]:
        return False
    meta = tree["paths"][path]
    meta["mode"] = mode
    meta["user"] = user
    meta["group"] = group
    return True


def reference_apply(scenario: str, seed: str, now: int) -> dict:
    scen_dir = Path(scenario) if str(scenario).startswith("/") else FIXTURES / scenario
    scen_name = Path(scenario).name if str(scenario).startswith("/") else scenario
    tree_file = scen_dir / "tree.json"
    rules_file = scen_dir / "rules.conf"
    tree = deepcopy(json.loads(tree_file.read_text(encoding="utf-8")))
    rules = parse_rules(rules_file)
    x_rules = [r for r in rules if r["type"] == "x"]
    actions: list[dict] = []

    for rule in rules:
        if rule["type"] == "o":
            if apply_ownership(rule["path"], rule["mode"], rule["user"], rule["group"], tree):
                actions.append(
                    {
                        "type": "ownership",
                        "path": rule["path"],
                        "user": rule["user"],
                        "group": rule["group"],
                    }
                )

    for rule in rules:
        if rule["type"] == "z":
            z_path = rule["path"]
            if pending_removals_under(z_path, rules, tree, now, x_rules):
                continue
            apply_recreate(z_path, rule["mode"], rule["user"], rule["group"], tree)
            actions.append({"type": "recreate", "path": z_path})
        elif rule["type"] == "r!":
            age_sec = rule.get("age") or 0
            glob_pat = rule["path"]
            for path in sorted(list(tree["paths"].keys())):
                if not globstar_match(glob_pat, path):
                    continue
                if is_excluded(path, rule.get("exclude_depth", 0), x_rules, glob_pat):
                    continue
                meta = tree["paths"][path]
                if age_eligible(meta, age_sec, now):
                    del tree["paths"][path]
                    actions.append({"type": "remove", "path": path})

    return {
        "scenario": scen_name,
        "seed": seed,
        "now": now,
        "surviving_paths": sorted(tree["paths"].keys()),
        "actions": actions,
    }


def merge_fragments(frag_dir: Path, mode: str) -> list[str]:
    lines: list[str] = []
    for name in sorted(os.listdir(frag_dir)):
        if not name.endswith(".conf"):
            continue
        tag = "boot-ex" if name.startswith("boot-ex.") else "boot"
        if mode == "boot" and tag == "boot-ex":
            continue
        if mode == "boot-ex" and tag not in ("boot", "boot-ex"):
            continue
        for raw in (frag_dir / name).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


def reference_generate(scenario: str, mode: str) -> dict:
    scen_dir = FIXTURES / scenario
    frag_dir = scen_dir / "fragments"
    rule_lines = merge_fragments(frag_dir, mode)
    return {
        "scenario": scenario,
        "mode": mode,
        "rule_lines": rule_lines,
        "line_count": len(rule_lines),
    }


def copy_scenario_tree(scenario: str) -> None:
    scen_dir = Path(scenario) if str(scenario).startswith("/") else FIXTURES / scenario
    if TREE.exists():
        shutil.rmtree(TREE)
    TREE.mkdir(parents=True)
    shutil.copy2(scen_dir / "tree.json", TREE / "tree.json")
