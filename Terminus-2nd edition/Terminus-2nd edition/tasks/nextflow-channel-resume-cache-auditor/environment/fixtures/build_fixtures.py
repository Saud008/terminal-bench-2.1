"""Build public Nextflow-like run fixtures for nfresume-audit."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
                rel = p.relative_to(run_dir).as_posix()
                paths.append(rel)
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
    (run_dir / "inputs" / "samples").mkdir(parents=True)
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
    SCENARIOS.mkdir(parents=True, exist_ok=True)
    seeds = {"seeds": ["alpha", "beta", "gamma", "delta"]}
    write_json(ROOT / "seeds.json", seeds)

    base_inputs = {
        "inputs/samples/b.fastq": "@readB\n",
        "inputs/samples/a.fastq": "@readA\n",
    }

    write_run(
        "clean-pipeline",
        {"run_id": "run-clean-001", "session_id": "sess-clean", "resumed": False},
        [
            {
                "task_id": "fetch:raw",
                "hash": "aa11",
                "parent_hashes": [],
                "container": "docker.io/ubuntu:22.04",
                "container_digest": "sha256:" + "a" * 64,
                "input_globs": ["inputs/samples/*.fastq"],
                "attempt": 1,
                "cached": False,
                "exit_status": 0,
                "output_hashes": {"raw.list": "sha256:" + "b" * 64},
            },
            {
                "task_id": "align:sample",
                "hash": "bb22",
                "parent_hashes": ["aa11"],
                "container": "quay.io/biocontainers/samtools:1.19",
                "container_digest": "sha256:" + "c" * 64,
                "input_globs": ["inputs/samples/a.fastq"],
                "attempt": 1,
                "cached": False,
                "exit_status": 0,
                "output_hashes": {"aligned.bam": "sha256:" + "d" * 64},
            },
        ],
        base_inputs,
    )

    write_run(
        "digest-drift",
        {"run_id": "run-drift-002", "session_id": "sess-drift", "resumed": True},
        [
            {
                "task_id": "call:variants",
                "hash": "cc33",
                "parent_hashes": ["bb22"],
                "container": "docker.io/gatk:4.4",
                "container_digest": "sha256:" + "e" * 64,
                "prior_digest": "sha256:" + "f" * 64,
                "input_globs": ["inputs/samples/*.fastq"],
                "attempt": 2,
                "cached": True,
                "exit_status": 0,
                "output_hashes": {"variants.vcf": "sha256:" + "1" * 64},
                "cache_session_id": "sess-drift",
            }
        ],
        base_inputs,
    )

    write_run(
        "glob-mismatch",
        {"run_id": "run-glob-003", "session_id": "sess-glob", "resumed": False},
        [
            {
                "task_id": "qc:reads",
                "hash": "dd44",
                "parent_hashes": [],
                "container": "docker.io/fastqc:0.12",
                "container_digest": "SHA256:" + ("0" * 64).upper(),
                "input_globs": ["inputs/samples/*.fastq"],
                "expansion_hash": "deadbeef" * 8,
                "attempt": 1,
                "cached": False,
                "exit_status": 0,
                "output_hashes": {"qc.html": "sha256:" + "2" * 64},
            }
        ],
        base_inputs,
    )

    write_run(
        "retry-stale",
        {"run_id": "run-retry-004", "session_id": "sess-retry", "resumed": True},
        [
            {
                "task_id": "index:genome",
                "hash": "ee55",
                "parent_hashes": [],
                "container": "docker.io/bwa:0.7",
                "container_digest": "sha256:" + "3" * 64,
                "input_globs": ["inputs/samples/a.fastq"],
                "attempt": 2,
                "cached": True,
                "exit_status": 0,
                "prior_digest": "sha256:" + "3" * 64,
                "prior_exit_status": 1,
                "output_hashes": {"genome.idx": "sha256:" + "4" * 64},
                "cache_session_id": "sess-retry",
            }
        ],
        {"inputs/samples/a.fastq": "@onlyA\n"},
    )

    write_run(
        "provenance-crossrun",
        {"run_id": "run-prov-005", "session_id": "sess-new-run", "resumed": True},
        [
            {
                "task_id": "merge:channels",
                "hash": "ff66",
                "parent_hashes": ["ee55"],
                "container": "docker.io/nextflow/k8s:23.10",
                "container_digest": "sha256:" + "5" * 64,
                "input_globs": ["inputs/samples/*.fastq"],
                "attempt": 1,
                "cached": True,
                "exit_status": 0,
                "output_hashes": {"merged.bam": "sha256:" + "6" * 64},
                "cache_session_id": "sess-old-run",
            }
        ],
        base_inputs,
    )

    write_run(
        "lineage-break",
        {"run_id": "run-lineage-006", "session_id": "sess-lineage", "resumed": False},
        [
            {
                "task_id": "link:parents",
                "hash": "ii99",
                "parent_hashes": ["aa11"],
                "lineage_digest": "0" * 64,
                "container": "docker.io/ubuntu:22.04",
                "container_digest": "sha256:" + "b" * 64,
                "input_globs": ["inputs/samples/a.fastq"],
                "attempt": 1,
                "cached": False,
                "exit_status": 0,
                "output_hashes": {"linked.txt": "sha256:" + "c" * 64},
            }
        ],
        {"inputs/samples/a.fastq": "@lineageA\n"},
    )

    scenario_map = {
        "clean-pipeline": "runs/clean-pipeline",
        "digest-drift": "runs/digest-drift",
        "glob-mismatch": "runs/glob-mismatch",
        "retry-stale": "runs/retry-stale",
        "provenance-crossrun": "runs/provenance-crossrun",
        "lineage-break": "runs/lineage-break",
    }
    for sid, rel in scenario_map.items():
        write_json(SCENARIOS / f"{sid}.json", {"run_dir": rel})

    print("fixtures built")


if __name__ == "__main__":
    main()
