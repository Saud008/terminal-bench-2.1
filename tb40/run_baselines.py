#!/usr/bin/env python3
"""Oracle/NOP baselines and per-fix ablation for a TB 4.0 task (checks 35, 36, 40, 73-76).

Baselines: harbor oracle x3 (the first with --force-build, i.e. a cold image
build) and nop x2, all with DOCKER_DEFAULT_PLATFORM=linux/amd64. The
<slug>/oracle-nop-evidence/ folders are replaced only when every oracle run
passes every test and every NOP run fails every test; otherwise the old
evidence is left alone and the failures are printed.

Ablation (--ablate): groups solve.sh's file writes by target file, and for each
target runs the oracle on a copy of the task whose solve.sh skips just that
file. Every ablation must drop the reward to 0 with at least one failing test.

Results are written to _reports/<slug>/baselines.json and ablation.json, bound
to the bundle sha; master_check.py reads them. Harbor job folders go to
_jobs/<slug>-baselines-<stamp>/ and _jobs/<slug>-ablate-<stamp>/.

Usage:
    py -3 tb40/run_baselines.py <slug-dir>            oracle x3 + nop x2
    py -3 tb40/run_baselines.py <slug-dir> --ablate   ablation only
    py -3 tb40/run_baselines.py <slug-dir> --all      baselines, then ablation
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import master_check as mc  # noqa: E402
import tb40_ship_check as ship  # noqa: E402

EVIDENCE_FILES = ("ctrf.json", "reward.txt", "test-stdout.txt")


def harbor(agent: str, task: Path, jobs: Path, name: str, force_build: bool) -> Path | None:
    cmd = ["harbor", "run", "-a", agent, "-p", str(task), "-o", str(jobs), "--job-name", name, "-y"]
    cmd.append("--force-build" if force_build else "--no-force-build")
    env = dict(os.environ, DOCKER_DEFAULT_PLATFORM="linux/amd64")
    print(f"  $ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (jobs / f"{name}.console.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    hits = sorted((jobs / name).glob("*/verifier/ctrf.json"))
    if not hits:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-5:]
        print(f"    no verifier output (rc={proc.returncode}): {' | '.join(tail)}")
        return None
    return hits[0].parent


def outcome(verifier: Path | None) -> dict:
    if verifier is None:
        return {"reward": None, "tests": 0, "passed": [], "failed": [], "error": "harbor produced no verifier output"}
    tests, summary = ship.ctrf_tests(json.loads((verifier / "ctrf.json").read_text(encoding="utf-8")))
    return {
        "reward": ship.read_reward(verifier / "reward.txt"),
        "tests": len(tests),
        "passed": [str(t.get("name", "")).split("::")[-1] for t in tests if t.get("status") == "passed"],
        "failed": [str(t.get("name", "")).split("::")[-1] for t in tests if t.get("status") != "passed"],
        "start": summary.get("start"),
    }


def baselines(outer: Path, sha: str, stamp: str) -> bool:
    slug, inner = outer.name, outer / outer.name
    jobs = mc.ROOT / "_jobs" / f"{slug}-baselines-{stamp}"
    jobs.mkdir(parents=True, exist_ok=True)
    plan = [("oracle-1", "oracle", True), ("oracle-2", "oracle", False), ("oracle-3", "oracle", False),
            ("nop-1", "nop", False), ("nop-2", "nop", False)]
    runs, dirs = [], {}
    for label, agent, force in plan:
        print(f"[{label}]", flush=True)
        ver = harbor(agent, inner, jobs, f"{slug}-{label}", force)
        res = outcome(ver)
        if agent == "oracle":
            res["ok"] = res["reward"] == 1.0 and res["tests"] > 0 and not res["failed"]
        else:
            res["ok"] = res["reward"] == 0.0 and res["tests"] > 0 and not res["passed"]
        print(f"    reward={res['reward']} passed={len(res['passed'])} failed={len(res['failed'])} {'OK' if res['ok'] else 'NOT OK'}")
        runs.append({"name": label, "job": str((jobs / f"{slug}-{label}").relative_to(mc.ROOT)), **res})
        dirs[label] = ver
    accepted = all(r["ok"] for r in runs)
    if accepted:
        ev = outer / "oracle-nop-evidence"
        for label, ver in dirs.items():
            dest = ev / label
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            for name in EVIDENCE_FILES:
                shutil.copy2(ver / name, dest / name)
        print(f"evidence replaced in {ev.relative_to(mc.ROOT)}")
    else:
        print("not every run behaved as required - oracle-nop-evidence/ left unchanged")
    record = {
        "bundle_sha": sha,
        "platform": "linux/amd64",
        "cold_build": True,
        "accepted": accepted,
        "runs": runs,
        "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    write_record(slug, "baselines.json", record)
    return accepted


def ablate(outer: Path, sha: str, stamp: str) -> bool:
    slug, inner = outer.name, outer / outer.name
    solve = (inner / "solution" / "solve.sh").read_text(encoding="utf-8")
    image = mc.ImageMap(inner / "environment")
    units = mc.ablation_units(mc.parse_solve(solve, image.workdir))
    if not units:
        print("no file writes recognised in solve.sh - nothing to ablate")
        return False
    base = mc.ROOT / "_jobs" / f"{slug}-ablate-{stamp}"
    jobs = base / "runs"
    jobs.mkdir(parents=True, exist_ok=True)
    lines = solve.split("\n")
    results = []
    for i, (target, touches) in enumerate(units.items(), 1):
        label = f"u{i:02d}-" + "".join(c if c.isalnum() else "-" for c in Path(target).name)[:40].strip("-")
        drop = {n for t in touches for n in range(t.start, t.end + 1)}
        copy = base / "tasks" / label / slug
        shutil.copytree(inner, copy, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc"))
        kept = [ln for n, ln in enumerate(lines, 1) if n not in drop]
        (copy / "solution" / "solve.sh").write_bytes("\n".join(kept).encode("utf-8"))
        print(f"[{label}] without {target} (solve.sh lines {min(drop)}-{max(drop)})", flush=True)
        res = outcome(harbor("oracle", copy, jobs, label, force_build=False))
        ok = res["reward"] == 0.0 and bool(res["failed"])
        print(f"    reward={res['reward']} failing={res['failed']} {'OK' if ok else 'NOT OK'}")
        results.append({
            "target": target,
            "lines": sorted(drop),
            "reward": res["reward"],
            "failed_tests": res["failed"],
            "ok": ok,
            **({"error": res["error"]} if res.get("error") else {}),
        })
    record = {"bundle_sha": sha, "units": results, "finished_at": dt.datetime.now().isoformat(timespec="seconds")}
    write_record(slug, "ablation.json", record)
    return all(u["ok"] for u in results)


def write_record(slug: str, name: str, record: dict) -> None:
    rep = mc.REPORTS / slug
    rep.mkdir(parents=True, exist_ok=True)
    (rep / name).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {(rep / name).relative_to(mc.ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug_dir")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--ablate", action="store_true", help="ablation only")
    group.add_argument("--all", action="store_true", help="baselines, then ablation")
    args = ap.parse_args()
    outer = ship.resolve_outer(args.slug_dir)
    if not (outer / outer.name).is_dir():
        print(f"not a delivery folder (<slug>/<slug>/ missing): {outer}")
        return 2
    if shutil.which("harbor") is None:
        print("harbor is not on PATH")
        return 2
    sha = ship.bundle_sha(outer / outer.name)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    ok = True
    if not args.ablate:
        ok = baselines(outer, sha, stamp) and ok
    if args.ablate or args.all:
        ok = ablate(outer, sha, stamp) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
