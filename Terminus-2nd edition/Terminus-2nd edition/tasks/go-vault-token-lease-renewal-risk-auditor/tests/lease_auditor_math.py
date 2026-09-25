"""Independent verifier math for vaultaud lease renewal risk auditing."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CONFIG = Path("/app/fixtures/config")
BUNDLED_TRANSCRIPTS = Path("/app/fixtures/renewal_logs")

ADMISSION_GRANTED = "granted"
ADMISSION_DENIED = "denied"
CYCLE_DEPTH = -1
CYCLE_PREFIX = "cycle:"
ORPHAN_PREFIX = "orphan:"
SCORE_CLAMP = 200
BUCKET_SEVERITY = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _sha_names(base: Path, names: list[str]) -> str:
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode("utf-8"))
        digest.update((base / name).read_bytes())
    return digest.hexdigest()


def bundled_config_sha256() -> str:
    return _sha_names(CONFIG, ["policies.json", "mounts.json", "roles.json", "audit_anchor.txt"])


def bundled_transcript_sha256() -> str:
    names = sorted(p.name for p in BUNDLED_TRANSCRIPTS.glob("*.lease-renew.jsonl"))
    return _sha_names(BUNDLED_TRANSCRIPTS, names)


def load_config() -> dict:
    return {
        "policies": json.loads((CONFIG / "policies.json").read_text(encoding="utf-8")),
        "mounts": json.loads((CONFIG / "mounts.json").read_text(encoding="utf-8")),
        "roles": json.loads((CONFIG / "roles.json").read_text(encoding="utf-8")),
        "anchor": (CONFIG / "audit_anchor.txt").read_text(encoding="utf-8").strip(),
    }


def load_events(tdir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(tdir.glob("*.lease-renew.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def applicable_revision(name: str, pol: dict, at: datetime) -> dict:
    """Pick the policy revision effective at issued_at (latest from <= at; later list entry on ties)."""
    revisions = pol["policies"][name]["revisions"]
    best = None
    best_at = None
    for rev in revisions:
        from_dt = _parse(rev["effective_from"])
        if from_dt > at:
            continue
        if best is None or from_dt >= best_at:
            best, best_at = rev, from_dt
    if best is None:
        raise KeyError(f"no applicable revision for {name}")
    return best


def resolve_policy(names: list[str], cfg: dict, at: datetime) -> tuple[int, bool]:
    """Walk each attached policy chain with override_parent stops; return min cap and deny_renew flag."""
    if not names:
        raise ValueError("no policies")
    pol = cfg["policies"]
    best_cap = 2**31 - 1
    deny = False
    for name in names:
        cap = 2**31 - 1
        cur = name
        seen: set[str] = set()
        while cur:
            if cur in seen:
                raise ValueError(f"policy cycle at {cur}")
            seen.add(cur)
            rev = applicable_revision(cur, pol, at)
            if rev.get("deny_renew"):
                deny = True
            if rev.get("override_parent"):
                cap = rev["max_ttl_sec"]
                break
            cap = min(cap, rev["max_ttl_sec"])
            cur = rev.get("parent") or ""
        best_cap = min(best_cap, cap)
    return best_cap, deny


def static_cap(ev: dict, policy_cap: int, cfg: dict) -> int:
    """Tightest positive TTL among request, mount, role, and resolved policy cap."""
    mount = cfg["mounts"]["mounts"][ev["mount"]]["max_lease_ttl_sec"]
    role = cfg["roles"]["roles"][ev["role"]]["max_ttl_sec"]
    return min(ev["lease_ttl_sec"], mount, role, policy_cap)


def lifetime_budget(ev: dict, origin: dict, cfg: dict) -> tuple[int, int]:
    """Return (lifetime ceiling, remaining budget) from origin issued_at and mount/role ceilings."""
    mount = cfg["mounts"]["mounts"][ev["mount"]]["max_token_lifetime_sec"]
    role = cfg["roles"]["roles"][ev["role"]]["max_token_lifetime_sec"]
    ceiling = min(mount, role)
    consumed = max(0, int((_parse(ev["issued_at"]) - _parse(origin["issued_at"])).total_seconds()))
    remaining = max(0, ceiling - consumed)
    return ceiling, remaining


def build_latest(events: list[dict]) -> dict[str, dict]:
    best: dict[str, dict] = {}
    for ev in events:
        prev = best.get(ev["token_id"])
        if prev is None or ev["renewal_seq"] > prev["renewal_seq"]:
            best[ev["token_id"]] = ev
    return best


def build_origin(events: list[dict]) -> dict[str, dict]:
    best: dict[str, dict] = {}
    for ev in events:
        prev = best.get(ev["token_id"])
        if prev is None or ev["renewal_seq"] < prev["renewal_seq"]:
            best[ev["token_id"]] = ev
    return best


def effective_parent(ev: dict) -> str:
    """Parent id for walks; orphan=true severs the edge and returns empty."""
    if ev.get("orphan"):
        return ""
    return ev.get("parent_id") or ""


def classify_lineage(ev: dict, latest: dict[str, dict]) -> dict:
    """Classify root/depth/orphan: severed orphan keeps token id; missing ancestor uses orphan: prefix."""
    parent = effective_parent(ev)
    if parent == "":
        return {
            "lineage_root": ev["token_id"],
            "lineage_depth": 0,
            "is_orphan": bool(ev.get("orphan")),
            "delegated_parent": "",
            "ancestors": [],
        }
    if parent not in latest:
        return {
            "lineage_root": ORPHAN_PREFIX + ev["token_id"],
            "lineage_depth": 0,
            "is_orphan": True,
            "delegated_parent": "",
            "ancestors": [],
        }
    visited = {ev["token_id"]}
    ancestors: list[str] = []
    cur = parent
    depth = 0
    while True:
        if cur in visited:
            smallest = min(visited)
            return {
                "lineage_root": CYCLE_PREFIX + smallest,
                "lineage_depth": CYCLE_DEPTH,
                "is_orphan": bool(ev.get("orphan")),
                "delegated_parent": "",
                "ancestors": ancestors,
            }
        row = latest.get(cur)
        if row is None:
            return {
                "lineage_root": ORPHAN_PREFIX + ev["token_id"],
                "lineage_depth": 0,
                "is_orphan": True,
                "delegated_parent": "",
                "ancestors": ancestors,
            }
        visited.add(cur)
        ancestors.append(cur)
        depth += 1
        nxt = effective_parent(row)
        if nxt == "":
            return {
                "lineage_root": cur,
                "lineage_depth": depth,
                "is_orphan": bool(ev.get("orphan")),
                "delegated_parent": parent,
                "ancestors": ancestors,
            }
        cur = nxt


def depth_key(depth: int) -> int:
    return 1 << 30 if depth < 0 else depth


def effective_renewable(row: dict, ev: dict, ancestors: list[str], latest: dict[str, dict],
                        cfg: dict, policy_denied: bool) -> bool:
    """True only when caller, mount, role, policy, admission, and all ancestors allow renewal."""
    if not ev["renewable"]:
        return False
    if not cfg["mounts"]["mounts"][ev["mount"]]["renewable"]:
        return False
    if not cfg["roles"]["roles"][ev["role"]]["renewable"]:
        return False
    if policy_denied:
        return False
    if row["admission"] != ADMISSION_GRANTED:
        return False
    for anc in ancestors:
        parent = latest.get(anc)
        if parent is None or not parent["renewable"]:
            return False
    return True


def reference_stage(tdir: Path) -> list[dict]:
    """Build the expected staging ledger: caps, budgets, delegation clamp, lineage, then sort."""
    cfg = load_config()
    events = load_events(tdir)
    latest = build_latest(events)
    origin = build_origin(events)

    staged: list[dict] = []
    meta: list[dict] = []
    for ev in events:
        org = origin[ev["token_id"]]
        at = _parse(ev["issued_at"])
        pol_cap, deny = resolve_policy(ev["policy_names"], cfg, at)
        static = static_cap(ev, pol_cap, cfg)
        ceiling, budget = lifetime_budget(ev, org, cfg)
        lin = classify_lineage(ev, latest)
        row = {
            "event_id": ev["event_id"],
            "token_id": ev["token_id"],
            "parent_id": ev["parent_id"],
            "renewal_seq": ev["renewal_seq"],
            "mount": ev["mount"],
            "role": ev["role"],
            "policy_cap_sec": pol_cap,
            "static_cap_sec": static,
            "lifetime_ceiling_sec": ceiling,
            "budget_remaining_sec": budget,
            "delegated_parent": lin["delegated_parent"],
            "granted_ttl_sec": 0,
            "admission": ADMISSION_DENIED,
            "effective_renewable": False,
            "lineage_root": lin["lineage_root"],
            "lineage_depth": lin["lineage_depth"],
            "is_orphan": lin["is_orphan"],
            "issued_at": ev["issued_at"],
        }
        staged.append(row)
        meta.append({"event": ev, "ancestors": lin["ancestors"], "deny": deny})

    order = sorted(
        range(len(staged)),
        key=lambda i: (
            depth_key(staged[i]["lineage_depth"]),
            staged[i]["renewal_seq"],
            staged[i]["token_id"],
            staged[i]["event_id"],
        ),
    )
    latest_idx: dict[str, int] = {}
    for i in order:
        row = staged[i]
        granted = min(row["static_cap_sec"], row["budget_remaining_sec"])
        parent = row["delegated_parent"]
        if parent:
            p = staged[latest_idx[parent]]
            headroom = max(
                0,
                int(
                    
                        _parse(p["issued_at"]).timestamp()
                        + p["granted_ttl_sec"]
                        - _parse(row["issued_at"]).timestamp()
                    
                ),
            )
            granted = min(granted, headroom)
        row["granted_ttl_sec"] = granted
        row["admission"] = ADMISSION_GRANTED if granted > 0 else ADMISSION_DENIED
        prev = latest_idx.get(row["token_id"])
        if prev is None or row["renewal_seq"] > staged[prev]["renewal_seq"]:
            latest_idx[row["token_id"]] = i

    for i, row in enumerate(staged):
        row["effective_renewable"] = effective_renewable(
            row, meta[i]["event"], meta[i]["ancestors"], latest, cfg, meta[i]["deny"]
        )

    staged.sort(
        key=lambda r: (
            depth_key(r["lineage_depth"]),
            r["renewal_seq"],
            r["token_id"],
            r["event_id"],
        )
    )
    return staged


def reference_risk(row: dict, anchor: str) -> dict:
    """Score one staged row against the audit anchor into risk_bucket / risk_score fields."""
    issued = _parse(row["issued_at"])
    anchor_dt = _parse(anchor)
    elapsed = max(0, int((anchor_dt - issued).total_seconds()))
    remaining = max(0, row["granted_ttl_sec"] - elapsed)
    if remaining <= 300:
        bucket, base = "critical", 100
    elif remaining <= 3600:
        bucket, base = "high", 70
    elif remaining <= 86400:
        bucket, base = "medium", 40
    else:
        bucket, base = "low", 10
    score = base
    if row["is_orphan"]:
        score += 50
    if not row["effective_renewable"]:
        score += 25
    if row["admission"] == ADMISSION_DENIED:
        score += 40
    if row["lineage_root"].startswith(CYCLE_PREFIX):
        score += 30
    score = min(score, SCORE_CLAMP)
    expires = _fmt(datetime.fromtimestamp(issued.timestamp() + row["granted_ttl_sec"], tz=timezone.utc))
    return {
        "token_id": row["token_id"],
        "renewal_seq": row["renewal_seq"],
        "lineage_root": row["lineage_root"],
        "lineage_depth": row["lineage_depth"],
        "is_orphan": row["is_orphan"],
        "admission": row["admission"],
        "risk_bucket": bucket,
        "risk_score": score,
        "seconds_remaining": remaining,
        "expires_at": expires,
    }


def lineage_edges(staged: list[dict]) -> list[dict]:
    """Emit unique parent→child edges for rows with a non-empty delegated_parent."""
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in staged:
        parent = row.get("delegated_parent") or ""
        if not parent:
            continue
        key = (parent, row["token_id"])
        if key in seen:
            continue
        seen.add(key)
        edges.append({"parent_token": key[0], "child_token": key[1]})
    edges.sort(key=lambda e: (e["parent_token"], e["child_token"]))
    return edges


def lineage_roots(staged: list[dict], risks: list[dict]) -> list[dict]:
    """Aggregate per lineage_root: counts, max score, severity-ordered worst_bucket, blast_radius."""
    groups: dict[str, dict] = {}
    for row, risk in zip(staged, risks, strict=True):
        g = groups.setdefault(
            row["lineage_root"],
            {"tokens": set(), "blast": set(), "row_count": 0, "max_score": 0, "worst": ""},
        )
        g["tokens"].add(row["token_id"])
        g["row_count"] += 1
        if row["lineage_depth"] > 0:
            g["blast"].add(row["token_id"])
        g["max_score"] = max(g["max_score"], risk["risk_score"])
        if BUCKET_SEVERITY.get(risk["risk_bucket"], 0) > BUCKET_SEVERITY.get(g["worst"], 0):
            g["worst"] = risk["risk_bucket"]
    out = []
    for root, g in groups.items():
        out.append(
            {
                "lineage_root": root,
                "token_count": len(g["tokens"]),
                "row_count": g["row_count"],
                "max_risk_score": g["max_score"],
                "worst_bucket": g["worst"],
                "blast_radius": len(g["blast"]),
            }
        )
    out.sort(key=lambda r: r["lineage_root"])
    return out


def reference_atlas(staged: list[dict], anchor: str) -> dict:
    """Assemble the expected token_risk_rollup.json document from staged rows."""
    risks_in_order = [reference_risk(r, anchor) for r in staged]
    tokens = sorted(risks_in_order, key=lambda t: (t["token_id"], t["renewal_seq"]))
    roots = lineage_roots(staged, risks_in_order)
    edges = lineage_edges(staged)
    seen = {t["token_id"] for t in tokens}
    totals = {
        "token_count": len(tokens),
        "distinct_token_count": len(seen),
        "orphan_count": sum(1 for t in tokens if t["is_orphan"]),
        "critical_count": sum(1 for t in tokens if t["risk_bucket"] == "critical"),
        "denied_count": sum(1 for t in tokens if t["admission"] == ADMISSION_DENIED),
        "cycle_count": sum(1 for t in tokens if t["lineage_root"].startswith(CYCLE_PREFIX)),
    }
    return {
        "tokens": tokens,
        "lineage_edges": edges,
        "lineage_roots": roots,
        "totals": totals,
    }
