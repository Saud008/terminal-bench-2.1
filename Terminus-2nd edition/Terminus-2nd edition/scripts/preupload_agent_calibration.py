#!/usr/bin/env python3
"""Pre-upload agent calibration — block EASY/TRIVIAL before zip.

Target bands (Snorkel Jun 2026 — worst model sets floor):
  HARD target (default new tasks): worst ≤20%, Opus ≤20%
  MEDIUM minimum (only if task.toml difficulty = medium): worst ≤60%

  python3 scripts/preupload_agent_calibration.py --task-dir tasks/<name>
  python3 scripts/preupload_agent_calibration.py --record --task-dir tasks/<name> \\
    --opus 1/5 --gpt 2/5 --post-harden
  python3 scripts/preupload_agent_calibration.py --pack-gate --task-dir tasks/<name>

First upload only (skips slugs in scripts/platform_submissions.txt).
Override (user explicit only): TERMINUS_AGENT_CALIBRATION_SKIP=1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

PLATFORM_FILE = REPO_ROOT / "scripts" / "platform_submissions.txt"

# Snorkel bands
HARD_TARGET_FLOOR = 0.20  # ≤20% = HARD training signal (repo default)
MEDIUM_MIN_FLOOR = 0.60  # >60% = EASY; need ≤60% for MEDIUM minimum
NOT_ACCEPTED_FLOOR = 0.80  # >80% = not accepted


def _slug(task_dir: Path) -> str:
    return task_dir.resolve().name


def _record_path(slug: str, *, mkdir: bool = False) -> Path:
    return jobs_path(f"agent-smoke-{slug}.json", mkdir=mkdir)


def _context_path(slug: str) -> Path:
    return resolve_jobs_path(f"trivial-easy-context-{slug}.json")


def _platform_slugs() -> set[str]:
    if not PLATFORM_FILE.is_file():
        return set()
    out: set[str] = set()
    for line in PLATFORM_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.split()[0])
    return out


def _read_task_difficulty(task_dir: Path) -> str:
    path = task_dir / "task.toml"
    if not path.is_file():
        return "hard"
    m = re.search(r'^\s*difficulty\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    if not m:
        return "hard"
    return m.group(1).strip().lower()


def _target_floor(task_dir: Path) -> tuple[float, float, str]:
    """Return (worst_max, opus_max, label)."""
    slug = _slug(task_dir)
    ctx = _load_platform_context(slug)
    if ctx and ctx.get("difficulty") in ("EASY", "TRIVIAL"):
        return HARD_TARGET_FLOOR, HARD_TARGET_FLOOR, "HARD_TARGET"
    diff = _read_task_difficulty(task_dir)
    if diff == "medium":
        return MEDIUM_MIN_FLOOR, MEDIUM_MIN_FLOOR, "MEDIUM_MIN"
    return HARD_TARGET_FLOOR, HARD_TARGET_FLOOR, "HARD_TARGET"


def _parse_rate(s: str) -> tuple[int, int, float]:
    """opus 4/5 | 80% | 0.8"""
    s = s.strip()
    m = re.match(r"^(\d+)/(\d+)$", s)
    if m:
        p, n = int(m.group(1)), int(m.group(2))
        return p, n, p / n if n else 1.0
    m = re.match(r"^(\d+(?:\.\d+)?)%$", s)
    if m:
        pct = float(m.group(1)) / 100.0
        return int(round(pct * 5)), 5, pct
    val = float(s)
    if val > 1:
        val /= 100.0
    return int(round(val * 5)), 5, val


def _worst_rate(data: dict) -> float:
    rates = []
    for key in ("opus", "gpt", "terminus-claude-opus-4-8", "terminus-gpt5-5"):
        entry = data.get(key)
        if isinstance(entry, dict) and "rate" in entry:
            rates.append(float(entry["rate"]))
        elif isinstance(entry, str):
            _, _, r = _parse_rate(entry)
            rates.append(r)
    return max(rates) if rates else 1.0


def _opus_rate(data: dict) -> float | None:
    entry = data.get("opus")
    if isinstance(entry, dict) and "rate" in entry:
        return float(entry["rate"])
    if isinstance(entry, str):
        _, _, r = _parse_rate(entry)
        return r
    return None


def _band_label(worst: float) -> str:
    if worst > NOT_ACCEPTED_FLOOR:
        return "NOT_ACCEPTED"
    if worst > MEDIUM_MIN_FLOOR:
        return "EASY"
    if worst > HARD_TARGET_FLOOR:
        return "MEDIUM"
    return "HARD"


def _load_platform_context(slug: str) -> dict | None:
    path = _context_path(slug)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def sync_smoke_from_platform_context(slug: str) -> Path | None:
    """Write agent-smoke from trivial-easy-context (platform EASY/TRIVIAL paste)."""
    ctx = _load_platform_context(slug)
    if not ctx or (not ctx.get("opus") and not ctx.get("gpt")):
        return None
    # Keep Case 6 post-harden smoke — do not clobber with pre-fix platform rates.
    existing = _record_path(slug)
    if existing.is_file():
        try:
            prev = json.loads(existing.read_text(encoding="utf-8"))
            if prev.get("post_harden") and str(prev.get("verdict", "")).upper() == "PASS":
                return existing
        except (json.JSONDecodeError, OSError):
            pass
    data: dict = {
        "slug": slug,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source": "platform_context",
        "platform_difficulty": ctx.get("difficulty", ""),
        "post_harden": False,
    }
    if ctx.get("opus"):
        p, n, r = _parse_rate(str(ctx["opus"]))
        data["opus"] = {"passed": p, "runs": n, "rate": r}
    if ctx.get("gpt"):
        p, n, r = _parse_rate(str(ctx["gpt"]))
        data["gpt"] = {"passed": p, "runs": n, "rate": r}
    worst = _worst_rate(data)
    data["worst_rate"] = worst
    data["band"] = _band_label(worst)
    out = _record_path(slug, mkdir=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return out


def _verdict(
    data: dict,
    task_dir: Path,
    *,
    post_harden: bool,
) -> tuple[str, str, float, float]:
    worst_max, opus_max, target_label = _target_floor(task_dir)
    worst = _worst_rate(data)
    opus = _opus_rate(data)
    reasons: list[str] = []

    ctx = _load_platform_context(_slug(task_dir))
    if ctx and ctx.get("difficulty") in ("EASY", "TRIVIAL") and not post_harden:
        reasons.append(
            f"platform {ctx['difficulty']} context — Case 6 harden then "
            "--record --opus N/5 --gpt N/5 --post-harden after local smoke"
        )

    if worst > worst_max:
        reasons.append(
            f"worst {worst:.0%} > {worst_max:.0%} ({target_label})"
        )
    if opus is not None and opus > opus_max and target_label == "HARD_TARGET":
        reasons.append(f"Opus {opus:.0%} > {opus_max:.0%} (Claude-primary HARD target)")

    if reasons:
        return "FAIL", "; ".join(reasons), worst_max, opus_max
    return "PASS", "", worst_max, opus_max


def cmd_record(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).resolve()
    slug = _slug(task_dir)
    data: dict = {
        "slug": slug,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "task_dir": str(task_dir),
        "post_harden": bool(args.post_harden),
        "source": "manual_record",
    }
    if args.opus:
        p, n, r = _parse_rate(args.opus)
        data["opus"] = {"passed": p, "runs": n, "rate": r}
    if args.gpt:
        p, n, r = _parse_rate(args.gpt)
        data["gpt"] = {"passed": p, "runs": n, "rate": r}
    if not args.opus and not args.gpt:
        print("ERROR: pass --opus and/or --gpt (e.g. --opus 1/5 --gpt 2/5)", file=sys.stderr)
        return 1

    worst = _worst_rate(data)
    data["worst_rate"] = worst
    data["band"] = _band_label(worst)
    verdict, reason, worst_max, _ = _verdict(data, task_dir, post_harden=bool(args.post_harden))
    data["verdict"] = verdict
    data["target"] = _target_floor(task_dir)[2]
    data["worst_max"] = worst_max
    if reason:
        data["fail_reason"] = reason

    out = _record_path(slug, mkdir=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Agent calibration: {verdict} — worst={worst:.0%} band={data['band']} — {out.relative_to(REPO_ROOT)}")
    if verdict == "FAIL":
        print(f"BLOCK upload — {reason}", file=sys.stderr)
        return 1
    return 0


def _skip_pack_gates(slug: str) -> bool:
    """Skip only for platform slugs with no pending EASY/TRIVIAL revision context."""
    if slug not in _platform_slugs():
        return False
    ctx = _load_platform_context(slug)
    if ctx and ctx.get("difficulty") in ("EASY", "TRIVIAL"):
        return False
    return True


def cmd_pack_gate(args: argparse.Namespace) -> int:
    if os.environ.get("TERMINUS_AGENT_CALIBRATION_SKIP") == "1":
        print("SKIP agent calibration (TERMINUS_AGENT_CALIBRATION_SKIP=1)")
        return 0
    task_dir = Path(args.task_dir).resolve()
    slug = _slug(task_dir)
    if _skip_pack_gates(slug):
        print(f"SKIP agent calibration — {slug} on platform, no EASY/TRIVIAL revise context")
        return 0

    # Platform EASY paste → sync smoke file so pack blocks even without manual --record
    sync_smoke_from_platform_context(slug)

    rec = resolve_jobs_path(f"agent-smoke-{slug}.json")
    if not rec.is_file():
        ctx = _load_platform_context(slug)
        if ctx and ctx.get("difficulty") in ("EASY", "TRIVIAL"):
            print(
                f"FAIL agent calibration — platform {ctx['difficulty']} on {slug}; "
                "no post-harden smoke. Case 6 + local Opus/GPT smoke, then "
                "--record --post-harden.",
                file=sys.stderr,
            )
            return 1
        print(
            f"FAIL agent calibration: no {rec.relative_to(REPO_ROOT)} — "
            "run local Opus+GPT smoke (≥2 runs each) then "
            "--record --opus N/5 --gpt N/5 --post-harden",
            file=sys.stderr,
        )
        return 1

    data = json.loads(rec.read_text(encoding="utf-8"))
    post_harden = bool(data.get("post_harden"))
    verdict, reason, worst_max, _ = _verdict(data, task_dir, post_harden=post_harden)
    worst = float(data.get("worst_rate", _worst_rate(data)))

    if verdict == "FAIL":
        print(f"FAIL agent calibration — {reason}", file=sys.stderr)
        print(
            f"  Policy: shared/no-easy-upload-lock.mdc — target {_target_floor(task_dir)[2]} "
            f"(worst ≤{worst_max:.0%})",
            file=sys.stderr,
        )
        return 1

    print(
        f"PASS agent calibration — worst {worst:.0%} ≤ {worst_max:.0%} "
        f"({'post-harden' if post_harden else 'pre-upload'})"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="deprecated alias — pack-gate is always strict for first upload",
    )
    parser.add_argument("--opus", help="e.g. 4/5 or 80%%")
    parser.add_argument("--gpt", help="e.g. 5/5 or 100%%")
    parser.add_argument(
        "--post-harden",
        action="store_true",
        help="After Case 6 — clears platform EASY block when rates meet HARD target",
    )
    parser.add_argument(
        "--sync-from-context",
        action="store_true",
        help="Write agent-smoke from jobs-local/trivial-easy-context-<slug>.json",
    )
    args = parser.parse_args()
    if args.sync_from_context:
        path = sync_smoke_from_platform_context(_slug(Path(args.task_dir)))
        if not path:
            print("WARN: no context to sync", file=sys.stderr)
            return 2
        print(path.relative_to(REPO_ROOT))
        return 0
    if args.record:
        return cmd_record(args)
    if args.pack_gate:
        return cmd_pack_gate(args)
    parser.error("use --record, --pack-gate, or --sync-from-context")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
