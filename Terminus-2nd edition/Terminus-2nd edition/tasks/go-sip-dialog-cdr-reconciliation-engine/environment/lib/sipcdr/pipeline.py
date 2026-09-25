"""sipcdrctl pipeline verbs — ingest → compile → rate → export."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sipcdr import dialogbuf
from sipcdr.compile import compile_dialogs
from sipcdr.load import load_scenario
from sipcdr.sqlite_pub import write_db
from sipcdr.window import rate_dialogs


def parse_flags(args: list[str]) -> tuple[str, str, str]:
    tenant = ""
    scenario = ""
    fixture_dir = os.environ.get("TB3_FIXTURE_DIR") or "/app/fixtures"
    i = 0
    while i < len(args):
        if args[i] == "--tenant":
            i += 1
            tenant = args[i]
        elif args[i] == "--scenario":
            i += 1
            scenario = args[i]
        elif args[i] == "--fixture-dir":
            i += 1
            fixture_dir = args[i]
        i += 1
    return tenant, scenario, fixture_dir


def scenario_dir(fixture_dir: str, scenario: str) -> Path:
    return Path(fixture_dir) / scenario


def ingest_transcript(args: list[str]) -> None:
    tenant, scenario, fixture_dir = parse_flags(args)
    msgs, pol = load_scenario(scenario_dir(fixture_dir, scenario))
    st: dict[str, Any] = {
        "tenant": tenant,
        "scenario": scenario,
        "messages": msgs,
        "policy": pol,
    }
    dialogbuf.write(dialogbuf.DEFAULT_PATH, st)


def compile_dialogs_cmd(args: list[str]) -> None:
    parse_flags(args)
    st = dialogbuf.read(dialogbuf.DEFAULT_PATH)
    st["dialogs"] = compile_dialogs(st.get("messages") or [], st.get("policy") or {})
    st["dialog_seal"] = dialogbuf.compute_seal(st)
    dialogbuf.write(dialogbuf.DEFAULT_PATH, st)


def rate_billing(args: list[str]) -> None:
    tenant, scenario, _ = parse_flags(args)
    st = dialogbuf.read(dialogbuf.DEFAULT_PATH)
    pol = st.get("policy") or {}
    st["dialogs"] = rate_dialogs(pol, st.get("dialogs") or {})
    rep = {
        "tenant": tenant,
        "scenario": scenario,
        "rated_count": len(st.get("dialogs") or {}),
        "window_hits": len(pol.get("windows") or []),
    }
    Path("/app/work").mkdir(parents=True, exist_ok=True)
    Path("/app/work/billing-window-report.json").write_text(
        json.dumps(rep, indent=2) + "\n", encoding="utf-8"
    )
    st["dialog_seal"] = dialogbuf.compute_seal(st)
    dialogbuf.write(dialogbuf.DEFAULT_PATH, st)


def export_cdr(args: list[str]) -> None:
    parse_flags(args)
    st = dialogbuf.read(dialogbuf.DEFAULT_PATH)
    db_path = "/app/output/cdr.sqlite"
    seal_path = "/app/output/cdr-publish-seal.json"
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    count = write_db(db_path, st.get("dialogs") or {})
    pol = st.get("policy") or {}
    seal = {
        "dialog_seal": st.get("dialog_seal", ""),
        "row_count": count,
        "billing_epoch": int(pol.get("clock_skew_ms") or 0),
    }
    Path(seal_path).write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
