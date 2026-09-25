"""Independent duel ledger reference math (Python sqlite3 and hashlib only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def read_admit_log_bundle(scenario_dir: Path) -> tuple[list[dict], dict]:
    msgs: list[dict] = []
    for path in sorted(scenario_dir.glob("*.duellog")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                msgs.append(json.loads(line))
    pol = json.loads((scenario_dir / "policy.json").read_text(encoding="utf-8"))
    return msgs, pol


def branch_identity(m: dict) -> str:
    if m.get("fork_tag"):
        return f"{m['duel_id']}|{m['lane_tag']}|{m['fork_tag']}"
    return f"{m['duel_id']}|{m['lane_tag']}"


def is_final_answer(code: int) -> bool:
    return 200 <= code < 300


def suppress_retransmits(msgs: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for m in sorted(msgs, key=lambda r: (r["ts_ms"], r["cseq"])):
        sig = (branch_identity(m), m.get("method", ""), m.get("status", 0), m["cseq"])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(m)
    return out


def shift_timestamps(msgs: list[dict], skew: int) -> list[dict]:
    out = []
    for m in msgs:
        c = dict(m)
        c["ts_ms"] = int(c["ts_ms"]) + int(skew)
        out.append(c)
    return out


def compile_branch_state(msgs: list[dict]) -> dict[str, dict]:
    matches: dict[str, dict] = {}
    for m in sorted(msgs, key=lambda r: (r["ts_ms"], r["cseq"])):
        key = branch_identity(m)
        d = matches.get(
            key,
            {
                "duel_id": m["duel_id"],
                "branch_key": key,
                "answered": False,
                "answer_ts_ms": 0,
                "end_ts_ms": 0,
                "disposition": "",
            },
        )
        if m.get("status", 0) > 0 and is_final_answer(m["status"]):
            d["answered"] = True
            if d["answer_ts_ms"] == 0:
                d["answer_ts_ms"] = m["ts_ms"]
        method = m.get("method") or ""
        if method == "FORFEIT" and not d["answered"]:
            d["end_ts_ms"] = m["ts_ms"]
            d["disposition"] = "forfeited"
        elif method == "RESIGN":
            if d["answered"] or d["disposition"] != "forfeited":
                d["end_ts_ms"] = m["ts_ms"]
                d["disposition"] = "completed" if d["answered"] else d["disposition"]
        matches[key] = d
    return matches


def score_band_for(pol: dict, answer_ts: int) -> str:
    minute = int((answer_ts // 60000) % 1440)
    for w in pol.get("windows", []):
        if w["start_minute"] <= minute <= w["end_minute"]:
            return w["tier"]
    return "calm"


def apply_score_bands(pol: dict, matches: dict[str, dict]) -> dict[str, dict]:
    out = {}
    for k, d in matches.items():
        c = dict(d)
        if c["answered"]:
            c["score_band"] = score_band_for(pol, c["answer_ts_ms"])
            if c["end_ts_ms"] > c["answer_ts_ms"]:
                c["duration_sec"] = (c["end_ts_ms"] - c["answer_ts_ms"]) / 1000.0
        out[k] = c
    return out


def reference_sqlite_rows(matches: dict[str, dict]) -> list[dict]:
    rows = []
    for k in sorted(matches):
        d = matches[k]
        if not d.get("answered"):
            continue
        if d.get("disposition") not in ("completed", "forfeited"):
            continue
        rows.append(
            {
                "duel_id": d["duel_id"],
                "branch_key": d["branch_key"],
                "answer_ts_ms": d["answer_ts_ms"],
                "end_ts_ms": d["end_ts_ms"],
                "duration_sec": d.get("duration_sec", 0.0),
                "score_band": d.get("score_band", ""),
                "disposition": d["disposition"],
            }
        )
    return rows


def reference_arena_sqlite(arena: str, scenario: str, fixture_root: Path) -> tuple[list[dict], dict]:
    msgs, pol = read_admit_log_bundle(fixture_root / scenario)
    msgs = suppress_retransmits(shift_timestamps(msgs, pol.get("clock_skew_ms", 0)))
    matches = apply_score_bands(pol, compile_branch_state(msgs))
    rows = reference_sqlite_rows(matches)
    seal_body = {"arena": arena, "scenario": scenario, "matches": matches}
    digest = hashlib.sha256(json.dumps(seal_body, sort_keys=True, default=str).encode()).hexdigest()
    seal = {"match_seal": digest, "row_count": len(rows), "score_epoch": pol.get("clock_skew_ms", 0)}
    return rows, seal
