"""Independent reference enforcer for casctl batch evaluation."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Policy:
    priority: int
    sub: str
    dom: str
    obj: str
    act: str
    eft: str


@dataclass
class Grouping:
    child: str
    parent: str
    dom: str


@dataclass
class Request:
    sub: str
    dom: str
    obj: str
    act: str


def order_bundles(seed: str, bundles: list[str]) -> list[str]:
    digest = hashlib.sha256(seed.encode()).digest()
    out = list(bundles)
    for i in range(len(out) - 1, 0, -1):
        j = digest[i % len(digest)] % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def select_bundles(seed: str, bundles: list[str]) -> list[str]:
    if not bundles:
        return []
    digest = hashlib.sha256(seed.encode()).digest()
    bits = digest[0] | (digest[1] << 8)
    selected = [b for i, b in enumerate(bundles) if (bits >> i) & 1]
    if not selected:
        selected = [bundles[digest[2] % len(bundles)]]
    return order_bundles(seed, selected)


def load_policies(path: Path) -> list[Policy]:
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    out: list[Policy] = []
    for row in rows[1:]:
        if len(row) < 6:
            continue
        out.append(Policy(int(row[0]), row[1], row[2], row[3], row[4], row[5]))
    return out


def load_groupings(path: Path) -> list[Grouping]:
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    out: list[Grouping] = []
    for row in rows[1:]:
        if len(row) < 3:
            continue
        out.append(Grouping(row[0], row[1], row[2]))
    return out


def load_engine(policies_root: Path, seed: str, bundles: list[str]) -> tuple[list[Policy], list[Grouping]]:
    policies: list[Policy] = []
    groupings: list[Grouping] = []
    for bundle in select_bundles(seed, bundles):
        policies.extend(load_policies(policies_root / bundle / "p.csv"))
        groupings.extend(load_groupings(policies_root / bundle / "g.csv"))
    return policies, groupings


def has_role(sub: str, role: str, dom: str, gs: list[Grouping]) -> bool:
    if sub == role:
        return True
    seen: set[str] = set()
    queue = [sub]
    while queue:
        cur = queue.pop(0)
        if cur == role:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        for g in gs:
            if g.dom == dom and g.child == cur and g.parent not in seen:
                queue.append(g.parent)
    return False


def key_match(obj: str, pattern: str) -> bool:
    return pattern == "*" or obj == pattern


def match_request(req: Request, pol: Policy, gs: list[Grouping]) -> bool:
    if req.dom != pol.dom:
        return False
    if not has_role(req.sub, pol.sub, req.dom, gs):
        return False
    if not key_match(req.obj, pol.obj):
        return False
    return key_match(req.act, pol.act)


def domain_policies(policies: list[Policy], dom: str) -> list[Policy]:
    return [p for p in policies if p.dom == dom]


def decide(matches: list[Policy]) -> str:
    has_allow = False
    for m in matches:
        if m.eft == "deny":
            return "deny"
        if m.eft == "allow":
            has_allow = True
    return "allow" if has_allow else "deny"


def load_requests(path: Path) -> list[Request]:
    out: list[Request] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        raw = json.loads(line)
        out.append(Request(raw["sub"], raw["dom"], raw["obj"], raw["act"]))
    return out


def fingerprint_policies(policies: list[Policy]) -> str:
    ordered = sorted(policies, key=lambda p: (p.priority, p.sub, p.dom, p.obj, p.act))
    lines = [f"{p.priority}|{p.sub}|{p.dom}|{p.obj}|{p.act}|{p.eft}" for p in ordered]
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()


def fingerprint_groupings(groupings: list[Grouping]) -> str:
    ordered = sorted(groupings, key=lambda g: (g.child, g.parent, g.dom))
    lines = [f"{g.child}|{g.parent}|{g.dom}" for g in ordered]
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()


def compute_audit_digest(
    bundles: list[str],
    policy_fp: str,
    grouping_fp: str,
    results: list[dict],
    stats: dict,
) -> str:
    parts = [policy_fp, grouping_fp, ",".join(bundles)]
    for row in results:
        parts.append(
            f"{row['sub']}|{row['dom']}|{row['obj']}|{row['act']}|{row['decision']}|{row['match_count']}"
        )
    parts.append(
        f"{stats['requests']}|{stats['allows']}|{stats['denies']}|"
        f"{stats['policies_loaded']}|{stats['groupings_loaded']}"
    )
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def reference_enforce(cfg_path: Path, requests_path: Path, fixtures_root: Path) -> dict:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    policies, groupings = load_engine(
        fixtures_root / "policies",
        cfg["seed"],
        cfg["bundles"],
    )
    ordered = sorted(policies, key=lambda p: (p.priority, p.sub))
    reqs = load_requests(requests_path)
    results = []
    allows = 0
    denies = 0
    for req in reqs:
        scope = domain_policies(ordered, req.dom)
        matches = [p for p in scope if match_request(req, p, groupings)]
        decision = decide(matches)
        if decision == "allow":
            allows += 1
        else:
            denies += 1
        results.append(
            {
                "sub": req.sub,
                "dom": req.dom,
                "obj": req.obj,
                "act": req.act,
                "decision": decision,
                "match_count": len(matches),
            }
        )
    stats = {
        "requests": len(reqs),
        "allows": allows,
        "denies": denies,
        "policies_loaded": len(policies),
        "groupings_loaded": len(groupings),
    }
    loaded_bundles = select_bundles(cfg["seed"], cfg["bundles"])
    policy_fp = fingerprint_policies(policies)
    grouping_fp = fingerprint_groupings(groupings)
    audit_digest = compute_audit_digest(loaded_bundles, policy_fp, grouping_fp, results, stats)
    return {
        "model": cfg["model"],
        "bundles": loaded_bundles,
        "results": results,
        "stats": stats,
        "audit_digest": audit_digest,
    }


def result_row(doc: dict, sub: str, dom: str, obj: str, act: str) -> dict:
    for row in doc["results"]:
        if row["sub"] == sub and row["dom"] == dom and row["obj"] == obj and row["act"] == act:
            return row
    raise KeyError((sub, dom, obj, act))
