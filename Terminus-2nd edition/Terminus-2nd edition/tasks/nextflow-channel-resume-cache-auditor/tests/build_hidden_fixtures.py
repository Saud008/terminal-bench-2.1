"""Build hidden nfresume-audit fixtures at verifier runtime (not shipped under /app)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(os.environ.get("NFRESUME_HIDDEN_ROOT", "/opt/verifier-fixtures/nfresume"))
RUNS = ROOT / "runs"
SCENARIOS = ROOT / "scenarios"


def norm_digest(raw: str) -> str:
    s = raw.strip()
    if s.lower().startswith("sha256:"):
        s = s[7:]
    return s.lower()


def expand_hash(run_dir: Path, globs: list[str]) -> str:
    h = hashlib.sha256()
    paths: list[str] = []
    for g in globs:
        for p in sorted(run_dir.glob(g)):
            if p.is_file():
                paths.append(p.relative_to(run_dir).as_posix())
    for p in sorted(paths):
        h.update(p.encode())
        h.update(b"\0")
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def write_run(name: str, meta: dict, tasks: list[dict], input_files: dict[str, str]) -> Path:
    run_dir = RUNS / name
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    write_json(run_dir / "run.meta.json", meta)
    (run_dir / "trace").mkdir()
    for rel, content in input_files.items():
        p = run_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    for task in tasks:
        tid = task["task_id"]
        fname = tid.replace(":", "_") + ".json"
        rec = dict(task)
        if not rec.get("expansion_hash"):
            rec["expansion_hash"] = expand_hash(run_dir, rec.get("input_globs", []))
        write_json(run_dir / "trace" / fname, rec)
        if task.get("cached"):
            work = run_dir / "work" / tid.replace(":", "_")
            work.mkdir(parents=True, exist_ok=True)
            marker = {
                "session_id": task.get("cache_session_id", meta["session_id"]),
                "stored_digest": norm_digest(task["container_digest"]),
                "task_id": tid,
            }
            write_json(work / ".nf_cached.json", marker)
    return run_dir


def main() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    RUNS.mkdir(parents=True)
    SCENARIOS.mkdir(parents=True)

    base_inputs = {
        "inputs/samples/b.fastq": "@readB\n",
        "inputs/samples/a.fastq": "@readA\n",
    }
    trap_inputs = dict(base_inputs)
    trap_inputs["inputs/samples/z-trap.fastq"] = "@trap\n"

    tmp = write_run(
        "_tmp-glob-base",
        {"run_id": "tmp", "session_id": "tmp", "resumed": False},
        [],
        base_inputs,
    )
    stale_glob_hash = expand_hash(tmp, ["inputs/samples/*.fastq"])
    shutil.rmtree(tmp)

    write_run(
        "glob-poison-trap",
        {"run_id": "run-trap-glob", "session_id": "sess-trap", "resumed": False},
        [
            {
                "task_id": "trap:glob",
                "hash": "gg77",
                "parent_hashes": [],
                "container": "docker.io/ubuntu:22.04",
                "container_digest": "sha256:" + "7" * 64,
                "input_globs": ["inputs/samples/*.fastq"],
                "expansion_hash": stale_glob_hash,
                "attempt": 1,
                "cached": False,
                "exit_status": 0,
                "output_hashes": {"out.txt": "sha256:" + "8" * 64},
            }
        ],
        trap_inputs,
    )

    write_run(
        "digest-drift-trap",
        {"run_id": "run-trap-drift", "session_id": "sess-trap-drift", "resumed": True},
        [
            {
                "task_id": "trap:digest",
                "hash": "hh88",
                "parent_hashes": [],
                "container": "docker.io/gatk:4.5",
                "container_digest": "sha256:" + "9" * 64,
                "prior_digest": "sha256:" + "8" * 64,
                "input_globs": ["inputs/samples/a.fastq"],
                "attempt": 2,
                "cached": True,
                "exit_status": 0,
                "output_hashes": {"out.vcf": "sha256:" + "a" * 64},
                "cache_session_id": "sess-trap-drift",
            }
        ],
        {"inputs/samples/a.fastq": "@trapA\n"},
    )

    for sid, rel in {
        "glob-poison-trap": "runs/glob-poison-trap",
        "digest-drift-trap": "runs/digest-drift-trap",
    }.items():
        write_json(SCENARIOS / f"{sid}.json", {"run_dir": rel})

    print("hidden fixtures built at", ROOT)


if __name__ == "__main__":
    main()
