from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_scenario(name: str, fixture_root: Path) -> dict:
    return json.loads((fixture_root / "scenarios" / f"{name}.json").read_text(encoding="utf-8"))


def _best_grant(expense: dict, grants: list[dict], aliases: dict[str, str]) -> dict | None:
    project = aliases.get(expense["project"], expense["project"])
    cands = []
    for g in grants:
        if g["project"] != project:
            continue
        if expense["category_path"].startswith(g["restriction_path"]):
            cands.append(g)
    if not cands:
        return None
    return sorted(cands, key=lambda g: len(g["restriction_path"]), reverse=True)[0]


def _eligible_delta(grant_id: str, grant_expense_dates: dict[str, str], amendments: list[dict]) -> int:
    cutoff = grant_expense_dates.get(grant_id, "")
    total = 0
    for a in amendments:
        if a["grant_id"] != grant_id:
            continue
        if cutoff and a["effective_date"] <= cutoff:
            total += int(a["delta_cents"])
    return total


def reference_atlas(name: str, fixture_root: Path, amendment_pass: int = 1) -> dict:
    sc = load_scenario(name, fixture_root)
    aliases = {x["alias"]: x["alias_of"] for x in sc.get("project_aliases", [])}
    grants = sc["grants"]
    grant_index = {g["grant_id"]: g for g in grants}
    spent: dict[str, int] = {g["grant_id"]: 0 for g in grants}
    last_date: dict[str, str] = {}
    rejections: list[dict] = []

    for e in sorted(sc["expenses"], key=lambda x: x["expense_id"]):
        g = _best_grant(e, grants, aliases)
        if g is None:
            rejections.append({"expense_id": e["expense_id"], "reason": "no_restriction_match"})
            continue
        if e["category"] not in g["allowed_categories"]:
            rejections.append({"expense_id": e["expense_id"], "reason": "category_rejected"})
            continue
        gid = g["grant_id"]
        spent[gid] += int(e["amount_cents"])
        last_date[gid] = max(last_date.get(gid, ""), e["expense_date"])

    balances = []
    for gid in sorted(grant_index):
        g = grant_index[gid]
        delta = _eligible_delta(gid, last_date, sc.get("amendments", []))
        remaining = int(g["ceiling_cents"]) + delta - spent[gid]
        balances.append(
            {
                "grant_id": gid,
                "spent_cents": spent[gid],
                "remaining_cents": remaining,
            }
        )

    digest_source = json.dumps(
        {
            "grant_balances": balances,
            "rejections": rejections,
            "amendment_pass": amendment_pass,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(digest_source).hexdigest()
    return {
        "grant_balances": balances,
        "rejections": rejections,
        "atlas_digest": digest,
        "amendment_pass": amendment_pass,
    }
