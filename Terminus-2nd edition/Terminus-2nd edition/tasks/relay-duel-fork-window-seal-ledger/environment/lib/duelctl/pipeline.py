"""duelctl pipeline verbs — admit → fold → score → seal."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from duelctl import matchbuf
from duelctl.compile import fold_branches
from duelctl.load import load_scenario
from duelctl.sqlite_pub import write_db
from duelctl.window import score_matches


def parse_flags(args: list[str]) -> tuple[str, str, str]:
    arena = ""
    scenario = ""
    fixture_dir = os.environ.get("TB3_FIXTURE_DIR") or "/app/fixtures"
    i = 0
    while i < len(args):
        if args[i] == "--arena":
            i += 1
            arena = args[i]
        elif args[i] == "--scenario":
            i += 1
            scenario = args[i]
        elif args[i] == "--fixture-dir":
            i += 1
            fixture_dir = args[i]
        i += 1
    return arena, scenario, fixture_dir


def scenario_dir(fixture_dir: str, scenario: str) -> Path:
    return Path(fixture_dir) / scenario


def admit_log(args: list[str]) -> None:
    arena, scenario, fixture_dir = parse_flags(args)
    msgs, pol = load_scenario(scenario_dir(fixture_dir, scenario))
    st: dict[str, Any] = {
        "arena": arena,
        "scenario": scenario,
        "messages": msgs,
        "policy": pol,
    }
    matchbuf.write(matchbuf.DEFAULT_PATH, st)


def fold_branches_cmd(args: list[str]) -> None:
    parse_flags(args)
    st = matchbuf.read(matchbuf.DEFAULT_PATH)
    st["matches"] = fold_branches(st.get("messages") or [], st.get("policy") or {})
    st["match_seal"] = matchbuf.compute_seal(st)
    matchbuf.write(matchbuf.DEFAULT_PATH, st)


def score_windows(args: list[str]) -> None:
    arena, scenario, _ = parse_flags(args)
    st = matchbuf.read(matchbuf.DEFAULT_PATH)
    pol = st.get("policy") or {}
    st["matches"] = score_matches(pol, st.get("matches") or {})
    rep = {
        "arena": arena,
        "scenario": scenario,
        "rated_count": len(st.get("matches") or {}),
        "window_hits": len(pol.get("windows") or []),
    }
    Path("/app/work").mkdir(parents=True, exist_ok=True)
    Path("/app/work/score-window-report.json").write_text(
        json.dumps(rep, indent=2) + "\n", encoding="utf-8"
    )
    st["match_seal"] = matchbuf.compute_seal(st)
    matchbuf.write(matchbuf.DEFAULT_PATH, st)


def seal_ledger(args: list[str]) -> None:
    parse_flags(args)
    st = matchbuf.read(matchbuf.DEFAULT_PATH)
    db_path = "/app/output/match-ledger.sqlite"
    seal_path = "/app/output/match-publish-seal.json"
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    count = write_db(db_path, st.get("matches") or {})
    pol = st.get("policy") or {}
    seal = {
        "match_seal": st.get("match_seal", ""),
        "row_count": count,
        "score_epoch": int(pol.get("clock_skew_ms") or 0),
    }
    Path(seal_path).write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
