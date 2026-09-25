"""wavehold CLI: scan -> compile -> publish rollout hold-preview stages.

Exit codes (see /app/docs/wavehold-cli.md):
  0  success
  2  usage / precondition failure (bad args, missing wave, missing run state)
  3  processing failure (corrupt wave JSONL, compile error)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from meridian.orchestrator import compile_atlas
from meridian.atlas import witness_of
from meridian.waveload import load_wave

APP = Path("/app")
STATE_ROOT = APP / "state" / "wavehold"
RUNS_ROOT = STATE_ROOT / "runs"
WITNESS_PATH = STATE_ROOT / "hold-witness.json"
DEFAULT_CONFIG = APP / "config" / "wavehold.json"
DEFAULT_ATLAS = APP / "output" / "mutation-rollout-atlas.json"


def _parse_flags(argv: List[str]) -> Dict[str, str]:
    flags: Dict[str, str] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--"):
            key = tok[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                flags[key] = argv[i + 1]
                i += 2
            else:
                flags[key] = ""
                i += 1
        else:
            i += 1
    return flags


def _run_dir(run_id: str) -> Path:
    return RUNS_ROOT / run_id


def _die(msg: str, code: int) -> int:
    sys.stderr.write(msg.rstrip() + "\n")
    return code


def cmd_scan(argv: List[str]) -> int:
    flags = _parse_flags(argv)
    run_id = flags.get("run-id")
    wave = flags.get("wave")
    config = flags.get("config", str(DEFAULT_CONFIG))
    if not run_id or not wave:
        return _die("scan: --wave and --run-id are required", 2)
    if not Path(wave).is_file():
        return _die(f"scan: wave file not found: {wave}", 2)
    try:
        records = load_wave(wave)
    except (json.JSONDecodeError, ValueError) as exc:
        return _die(f"scan: corrupt wave JSONL: {exc}", 3)
    if not Path(config).is_file():
        return _die(f"scan: config not found: {config}", 2)

    run_dir = _run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    norm = run_dir / "wave.jsonl"
    with norm.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")
    meta = {
        "run_id": run_id,
        "wave": str(Path(wave).resolve()),
        "config": str(Path(config).resolve()),
        "record_count": len(records),
    }
    (run_dir / "run-meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


def cmd_compile(argv: List[str]) -> int:
    flags = _parse_flags(argv)
    run_id = flags.get("run-id")
    if not run_id:
        return _die("compile: --run-id is required", 2)
    run_dir = _run_dir(run_id)
    meta_path = run_dir / "run-meta.json"
    if not meta_path.is_file():
        return _die(f"compile: no scanned run state for run-id {run_id}", 2)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    wave = str(run_dir / "wave.jsonl")
    config = meta.get("config", str(DEFAULT_CONFIG))
    try:
        atlas = compile_atlas(config, wave)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        return _die(f"compile: processing failure: {exc}", 3)

    (run_dir / "rollout-ledger.json").write_text(
        json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    WITNESS_PATH.write_text(
        json.dumps(witness_of(atlas), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


def cmd_publish(argv: List[str]) -> int:
    flags = _parse_flags(argv)
    run_id = flags.get("run-id")
    if not run_id:
        return _die("publish: --run-id is required", 2)
    run_dir = _run_dir(run_id)
    ledger_path = run_dir / "rollout-ledger.json"
    if not ledger_path.is_file():
        return _die(f"publish: run {run_id} has not been compiled", 2)
    out = Path(flags.get("output") or str(DEFAULT_ATLAS))
    out.parent.mkdir(parents=True, exist_ok=True)
    atlas = json.loads(ledger_path.read_text(encoding="utf-8"))
    out.write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _die("usage: wavehold scan|compile|publish ...", 2)
    cmd, rest = argv[0], argv[1:]
    if cmd == "scan":
        return cmd_scan(rest)
    if cmd == "compile":
        return cmd_compile(rest)
    if cmd == "publish":
        return cmd_publish(rest)
    return _die(f"wavehold: unknown subcommand {cmd!r}", 2)


if __name__ == "__main__":
    raise SystemExit(main())
