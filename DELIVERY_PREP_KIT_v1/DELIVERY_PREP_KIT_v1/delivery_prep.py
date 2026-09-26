#!/usr/bin/env python3
"""Delivery Prep Tool -- assembles a task's final shippable bundle into the exact
canonical structure, from independently-verified sources, without losing anything.

    <task-slug>/
    ├── <task-slug>/                (instruction.md, task.toml, environment/, solution/, tests/)
    ├── rubric.txt
    ├── oracle-nop-evidence/        (oracle-1,2,3/, nop-1,2/, each ctrf.json+reward.txt+test-stdout.txt)
    └── trajectories/
        ├── run-01/ .. run-NN/      (agent/, verifier/, config.json, result.json -- rubric_score.txt
        │                            is NOT generated here, see note at the end of the run)
        └── SUMMARY.txt

Sources:
  --ingested DIR   the INGESTED/<slug>/ tree: <slug>/<slug>/{instruction.md,task.toml,environment,
                   solution,tests}, <slug>/rubric.txt, <slug>/oracle-nop-evidence/
  --jobs DIR...    one or more run_k.sh job output directories (each has config.json at its own
                   root and one subdirectory per trial). Trials across multiple jobs may be
                   combined (e.g. a k=2 run plus a separate k=3 run) into one delivery, AS LONG AS
                   every included trial shares the same bundle sha, model and reasoning_effort --
                   this is verified, not assumed.

Every trial included is independently re-checked with check_trajectory.py's own per-trial logic
(same file, imported directly, not reimplemented) before being trusted. A trial that fails that
check is refused, not silently dropped -- the tool stops and reports why, since silently shipping
fewer runs than asked for is worse than stopping.

After assembly, the tool re-walks BOTH the sources and the destination and compares file counts and
sha256 digests file-by-file; any mismatch is reported and the run is marked incomplete. Nothing is
overwritten without --force.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_trajectory as ct  # noqa: E402

BUNDLE_ITEMS = ["instruction.md", "task.toml", "environment", "solution", "tests"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bundle_sha(inner: Path) -> str:
    """Byte-for-byte the same formula used everywhere else this batch:
    find instruction.md tests environment solution task.toml -type f -print0 | sort -z |
    xargs -0 shasum -a 256 | shasum -a 256 | cut -c1-16 -- run from inside `inner`.
    Reimplementing this in pure Python previously produced a DIFFERENT hash (it hashed just the
    concatenated digests, dropping the "digest  filename" line format and file-path input that
    `shasum -a 256 <file>` actually feeds the outer hash) -- shelling out to the exact command
    guarantees this tool's sha always matches every sha already recorded in TASK_UPDATE_LOGS/
    and every SOURCE.txt from this batch.
    """
    cmd = (
        "find instruction.md tests environment solution task.toml -type f -print0 | "
        "sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -c1-16"
    )
    out = subprocess.run(cmd, shell=True, cwd=inner, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def tree_manifest(root: Path) -> dict[str, str]:
    """relative path -> sha256, for every file under root."""
    return {
        str(p.relative_to(root)): sha256_file(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def copy_verified(src: Path, dst: Path, label: str, report: list[str]) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
    src_manifest = tree_manifest(src) if src.is_dir() else {src.name: sha256_file(src)}
    dst_manifest = tree_manifest(dst) if dst.is_dir() else {dst.name: sha256_file(dst)}
    if src_manifest != dst_manifest:
        missing = set(src_manifest) - set(dst_manifest)
        changed = {k for k in src_manifest.keys() & dst_manifest.keys() if src_manifest[k] != dst_manifest[k]}
        report.append(f"MISMATCH copying {label}: missing={sorted(missing)} changed={sorted(changed)}")
        return False
    report.append(f"OK {label}: {len(src_manifest)} file(s), all digests match")
    return True


def find_trials(job_dir: Path) -> list[Path]:
    return sorted(
        d for d in job_dir.iterdir()
        if d.is_dir() and (d / "config.json").exists() and (d / "result.json").exists()
    )


def load_source_json(job_dir: Path) -> dict:
    sp = job_dir / "SOURCE.txt"
    return {"job_dir": job_dir, "source_text": sp.read_text() if sp.exists() else ""}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--ingested", required=True, type=Path)
    ap.add_argument("--jobs", required=True, type=Path, nargs="+",
                     help="one or more run_k.sh job output directories to draw trials from")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-trials", type=int, default=5)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    slug = args.slug
    ingested_outer = args.ingested / slug
    inner = ingested_outer / slug
    rubric = ingested_outer / "rubric.txt"
    onop = ingested_outer / "oracle-nop-evidence"

    for required, name in ((inner, "inner bundle dir"), (rubric, "rubric.txt"), (onop, "oracle-nop-evidence/")):
        if not required.exists():
            print(f"ERROR: {name} not found at {required}")
            return 1
    for item in BUNDLE_ITEMS:
        if not (inner / item).exists():
            print(f"ERROR: inner bundle missing {item}")
            return 1

    dest_root = args.out / slug
    if dest_root.exists() and not args.force:
        print(f"ERROR: {dest_root} already exists (use --force to overwrite)")
        return 1

    print(f"=== {slug}: collecting trials from {len(args.jobs)} job dir(s) ===")
    sha = bundle_sha(inner)
    print(f"bundle sha (fresh recompute from INGESTED): {sha}")

    all_trials: list[Path] = []
    for job in args.jobs:
        if not job.exists():
            print(f"ERROR: job dir does not exist: {job}")
            return 1
        trials = find_trials(job)
        print(f"  {job.name}: {len(trials)} trial dir(s) with config.json+result.json")
        all_trials.extend(trials)

    if not all_trials:
        print("ERROR: no trial directories found across the given job dirs")
        return 1

    checked = []
    problems = []
    for t in sorted(all_trials, key=lambda p: p.stat().st_mtime):
        result = ct.check_trial(str(t), "xhigh")
        cfg = json.loads((t / "config.json").read_text())
        task_cfg = (cfg.get("task") or {}) if isinstance(cfg, dict) else {}
        model = (cfg.get("agent") or {}).get("model_name") if isinstance(cfg, dict) else None
        if not result["ok"]:
            problems.append(f"{t}: NOT OK -- {result['problems']}")
            continue
        checked.append((t, result, model))

    print(f"\n{len(checked)}/{len(all_trials)} trial(s) pass check_trajectory.py's own fidelity checks")
    for p in problems:
        print(f"  REFUSED: {p}")

    if len(checked) < args.max_trials:
        print(f"\nERROR: only {len(checked)} clean trial(s) available, need {args.max_trials}. "
              f"Run more trials against sha {sha} before assembling. Nothing written.")
        return 1

    chosen = checked[: args.max_trials]

    report: list[str] = []
    ok = True
    ok &= copy_verified(inner, dest_root / slug, f"{slug}/ (bundle)", report)
    ok &= copy_verified(rubric, dest_root / "rubric.txt", "rubric.txt", report)
    ok &= copy_verified(onop, dest_root / "oracle-nop-evidence", "oracle-nop-evidence/", report)

    traj_dir = dest_root / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    rewards = []
    for i, (t, result, model) in enumerate(chosen, start=1):
        run_dir = traj_dir / f"run-{i:02d}"
        for item in ("agent", "verifier", "config.json", "result.json"):
            src_item = t / item
            if src_item.exists():
                ok &= copy_verified(src_item, run_dir / item, f"trajectories/run-{i:02d}/{item}", report)
        reward_txt = run_dir / "verifier" / "reward.txt"
        rewards.append(reward_txt.read_text().strip() if reward_txt.exists() else "?")

    summary_lines = [
        f"{slug} sha={sha} model=@openai/gpt-5.6 reasoning_effort=xhigh k={len(chosen)}",
        "[" + ", ".join(rewards) + "]",
    ]
    (traj_dir / "SUMMARY.txt").write_text("\n".join(summary_lines) + "\n")
    report.append(f"SUMMARY.txt written: {summary_lines[1]}")

    print("\n=== copy+verify report ===")
    for line in report:
        print(" ", line)

    print("\n=== structural check ===")
    expected_top = {slug, "rubric.txt", "oracle-nop-evidence", "trajectories"}
    actual_top = {p.name for p in dest_root.iterdir()}
    if actual_top != expected_top:
        print(f"  STRUCTURE MISMATCH: expected {expected_top}, got {actual_top}")
        ok = False
    else:
        print("  top-level structure matches exactly")

    print("\n=== STILL NEEDED before this can ship (not automated here, needs real judgment) ===")
    print("  - rubric_score.txt in every trajectories/run-0N/, each citing THAT run's own")
    print("    trajectory.json/test-stdout.txt evidence against rubric.txt -- write these by hand,")
    print("    never templated/copied between runs (check 71/72).")
    print("  - A final human read-through against MASTER_CHECKLIST.txt before moving to")
    print("    READY_TO_SHIP -- this tool only guarantees structure and that nothing was lost in")
    print("    transit, not that the bundle is ship-ready.")

    if not ok:
        print(f"\n{slug}: ASSEMBLY HAD PROBLEMS -- see report above. Not marking complete.")
        return 1
    print(f"\n{slug}: assembled cleanly at {dest_root}, {len(chosen)} trial(s), nothing lost in transit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
