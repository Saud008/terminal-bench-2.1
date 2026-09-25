"""Independent reference math for filingatlas redaction risk atlas."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


def sealed_bias() -> float:
    raw = os.environ.get("TB3_SEALED_BIAS")
    if raw:
        try:
            v = float(raw)
            if v > 0:
                return v
        except ValueError:
            pass
    return 1.0


def load_scenario(scenario: str, fixture_root: Path) -> tuple[list, list, list, list, dict]:
    base = fixture_root / "scenarios" / scenario
    dockets = []
    for line in (base / "dockets.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            dockets.append(json.loads(line))
    parties = json.loads((base / "parties.json").read_text(encoding="utf-8"))["parties"]
    pages = []
    for line in (base / "pages.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            pages.append(json.loads(line))
    pages.sort(key=lambda p: p["page_num"])
    sealed = json.loads((base / "sealed_terms.json").read_text(encoding="utf-8"))["terms"]
    policy = json.loads((base / "policy.json").read_text(encoding="utf-8"))
    return dockets, parties, pages, sealed, policy


def normalize_term(term: str) -> str:
    t = term.strip().lower()
    t = re.sub(r"[-\s]+", " ", t)
    return t.strip()


def matches_sealed(page_text: str, sealed_term: str) -> bool:
    norm_page = normalize_term(page_text)
    norm_term = normalize_term(sealed_term)
    return norm_term in norm_page


_base_exhibit = re.compile(r"(?i)Exhibit\s+(\d+)(?:-([A-Za-z]+))?(?:\s+(IV|III|II|I|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I))?")


def parse_exhibit_refs(text: str) -> list[str]:
    out: list[str] = []
    for m in _base_exhibit.finditer(text):
        base = f"Exhibit {m.group(1)}"
        if m.group(2):
            base = f"{base}-{m.group(2)}"
        if m.group(3):
            base = f"{base} {m.group(3)}"
        out.append(base)
    seen: set[str] = set()
    deduped: list[str] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def resolve_aliases(parties: list[dict]) -> dict[str, list[str]]:
    graph: dict[str, set[str]] = {p["id"]: set() for p in parties}
    for p in parties:
        for alias in p.get("aliases", []):
            graph[p["id"]].add(alias)
    changed = True
    while changed:
        changed = False
        for p in parties:
            pid = p["id"]
            for alias in list(graph[pid]):
                for other in parties:
                    if other["name"] == alias or alias in other.get("aliases", []):
                        for a in other.get("aliases", []):
                            if a not in graph[pid]:
                                graph[pid].add(a)
                                changed = True
                        if other["name"] not in graph[pid]:
                            graph[pid].add(other["name"])
                            changed = True
    return {k: sorted(v) for k, v in graph.items()}


def pick_primary_docket(dockets: list[dict]) -> str:
    for d in dockets:
        if d.get("primary_flag"):
            return str(d["number"]).strip()
    if not dockets:
        return ""
    return sorted(dockets, key=lambda x: x.get("filed_at", ""), reverse=True)[0]["number"].strip()


def locate_line(page: dict, needle: str) -> tuple[int, int]:
    for ln in page.get("lines", []):
        if matches_sealed(ln.get("text", ""), needle):
            return page["page_num"], ln.get("line_num", 0)
    return page["page_num"], 0


def match_party(text: str, parties: list[dict], resolved: dict[str, list[str]]) -> str:
    lower = text.lower()
    for p in parties:
        if p["name"].lower() in lower:
            return p["id"]
    for p in parties:
        for alias in resolved.get(p["id"], []):
            if alias.lower() in lower:
                return p["id"]
    return ""


def reference_findings(scenario: str, fixture_root: Path) -> list[dict]:
    dockets, parties, pages, sealed, _policy = load_scenario(scenario, fixture_root)
    resolved = resolve_aliases(parties)
    docket = pick_primary_docket(dockets)
    out: list[dict] = []
    seq = 0
    for page in pages:
        for ln in page.get("lines", []):
            text = ln.get("text", "")
            for term in sealed:
                if not matches_sealed(text, term["term"]):
                    continue
                seq += 1
                exhibits = parse_exhibit_refs(text)
                exhibit_ref = exhibits[0] if exhibits else ""
                party_id = match_party(text, parties, resolved)
                page_num, line_num = page["page_num"], ln.get("line_num", 0)
                out.append({
                    "finding_id": f"F-{seq:03d}",
                    "party_id": party_id,
                    "exhibit_ref": exhibit_ref,
                    "term": term["term"],
                    "risk_level": "high",
                    "page": page_num,
                    "line": line_num,
                    "docket": docket,
                })
    out.sort(key=lambda f: f["finding_id"])
    return out


def _sorted_json(value: object) -> object:
    if isinstance(value, dict):
        return {k: _sorted_json(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_sorted_json(v) for v in value]
    return value


def reference_bundle_digest(scenario: str, fixture_root: Path) -> str:
    dockets, parties, pages, sealed, policy = load_scenario(scenario, fixture_root)
    payload = _sorted_json(
        {
            "dockets": dockets,
            "pages": pages,
            "parties": parties,
            "policy": policy,
            "scenario": scenario,
            "sealed_terms": sealed,
        }
    )
    data = json.dumps(payload, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def reference_atlas_report(scenario: str, fixture_root: Path) -> dict:
    findings = reference_findings(scenario, fixture_root)
    report = {"scenario": scenario, "finding_count": len(findings), "findings": findings}
    payload = _sorted_json(
        {
            "finding_count": report["finding_count"],
            "findings": report["findings"],
            "scenario": report["scenario"],
        }
    )
    data = json.dumps(payload, separators=(",", ":")).encode()
    report["atlas_digest"] = hashlib.sha256(data).hexdigest()
    return report
