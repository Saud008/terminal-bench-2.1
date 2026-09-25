from __future__ import annotations

import sys

from snapret import bridge


def _usage() -> None:
    print(
        "snapretctl import-graph --scenario SCENARIO [--fixture-dir D]",
        file=sys.stderr,
    )
    print("snapretctl score-retention --scenario SCENARIO", file=sys.stderr)
    print(
        "snapretctl publish-audit --scenario SCENARIO "
        "[--output-report PATH] [--output-dangling PATH]",
        file=sys.stderr,
    )


def _parse_flags(args: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    idx = 0
    while idx < len(args):
        token = args[idx]
        if not token.startswith("--"):
            raise ValueError(f"unknown flag {token}")
        key = token[2:]
        if idx + 1 >= len(args):
            raise ValueError(f"missing value for --{key}")
        out[key] = args[idx + 1]
        idx += 2
    return out


def main() -> None:
    if len(sys.argv) < 2:
        _usage()
        raise SystemExit(2)
    cmd = sys.argv[1]
    try:
        if cmd == "import-graph":
            _run_import_graph(sys.argv[2:])
        elif cmd == "score-retention":
            _run_score_retention(sys.argv[2:])
        elif cmd == "publish-audit":
            _run_publish_audit(sys.argv[2:])
        else:
            _usage()
            raise SystemExit(2)
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc


def _run_import_graph(args: list[str]) -> None:
    flags = _parse_flags(args)
    scenario = flags.get("scenario", "")
    fixture_dir = flags.get("fixture-dir", "/app/fixtures")
    if not scenario:
        raise ValueError("--scenario required")
    stage = bridge.materialize_fleet_graph(scenario, fixture_dir)
    bridge.persist_fleet_graph(stage)


def _run_score_retention(args: list[str]) -> None:
    flags = _parse_flags(args)
    scenario = flags.get("scenario", "")
    if not scenario:
        raise ValueError("--scenario required")
    bridge.run_analyze_pass(scenario)


def _run_publish_audit(args: list[str]) -> None:
    flags = _parse_flags(args)
    scenario = flags.get("scenario", "")
    if not scenario:
        raise ValueError("--scenario required")
    bridge.seal_retention_report(
        scenario,
        flags.get("output-report", ""),
        flags.get("output-dangling", ""),
    )


if __name__ == "__main__":
    main()
