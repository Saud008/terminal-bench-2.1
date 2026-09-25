"""routeleaklab CLI."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from routeleak_lab.pipeline import evaluate_experiment


def _read_scale() -> float:
    env_v = os.environ.get("TB3_FEATURE_SCALE")
    if env_v is not None and env_v != "":
        return float(env_v)
    cfg = Path("/app/config/routeleaklab.json")
    if cfg.is_file():
        data = json.loads(cfg.read_text(encoding="utf-8"))
        return float(data.get("feature_scale", 1.0))
    return 1.0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "evaluate":
        print("usage: routeleaklab evaluate --experiment <name> --report <path> [--run-id <id>]", file=sys.stderr)
        return 1
    experiment = ""
    report = "/app/output/routeleak_eval_report.json"
    run_id = "default"
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--experiment" and i + 1 < len(args):
            experiment = args[i + 1]
            i += 2
        elif args[i] == "--report" and i + 1 < len(args):
            report = args[i + 1]
            i += 2
        elif args[i] == "--run-id" and i + 1 < len(args):
            run_id = args[i + 1]
            i += 2
        else:
            print("usage: routeleaklab evaluate --experiment <name> --report <path> [--run-id <id>]", file=sys.stderr)
            return 1
    if not experiment:
        print("usage: routeleaklab evaluate --experiment <name> --report <path> [--run-id <id>]", file=sys.stderr)
        return 1
    exp_dir = Path("/app/fixtures/experiments") / experiment
    if not exp_dir.is_dir():
        print("missing experiment", file=sys.stderr)
        return 2
    try:
        evaluate_experiment(
            exp_dir,
            experiment=experiment,
            run_id=run_id,
            feature_scale=_read_scale(),
            snapshot_path=Path("/app/state/eval-snapshot.json"),
            report_path=Path(report),
        )
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid experiment: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
