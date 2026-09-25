#!/usr/bin/env python3
"""Independent GNU parallel joblog / .par parser for verifier (not used by /app toolchain)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

USER_HZ = 100


@dataclass(frozen=True)
class ParRecord:
    seq: int
    slot: int
    exit_code: int
    utime_jiffies: int
    stime_jiffies: int
    wall_sec: float
    start_epoch: float
    end_epoch: float


def parse_joblog_rows(joblog: Path) -> list[tuple[int, str, int, str]]:
    lines = joblog.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str, int, str]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 9:
            continue
        seq = int(parts[0])
        host = parts[1]
        exitval = int(parts[6])
        command = "\t".join(parts[8:])
        rows.append((seq, host, exitval, command))
    return rows


def parse_par_file(par_path: Path) -> ParRecord:
    data: dict[str, str] = {}
    for line in par_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return ParRecord(
        seq=int(data["seq"]),
        slot=int(data["slot"]),
        exit_code=int(data["exit"]),
        utime_jiffies=int(data.get("utime_jiffies", 0)),
        stime_jiffies=int(data.get("stime_jiffies", 0)),
        wall_sec=float(data.get("wall_sec", 0)),
        start_epoch=float(data["start_epoch"]),
        end_epoch=float(data["end_epoch"]),
    )


def load_par_dir(par_dir: Path) -> dict[int, ParRecord]:
    out: dict[int, ParRecord] = {}
    for par in sorted(par_dir.glob("*.par")):
        rec = parse_par_file(par)
        out[rec.seq] = rec
    return out


def authoritative_exit(joblog_exit: int, par: ParRecord | None) -> int:
    if par is not None:
        return par.exit_code
    return joblog_exit


def exit_histogram_from_run(joblog: Path, par_dir: Path) -> dict[str, int]:
    pars = load_par_dir(par_dir)
    hist: dict[str, int] = {}
    for seq, _host, exitval, _cmd in parse_joblog_rows(joblog):
        code = authoritative_exit(exitval, pars.get(seq))
        key = str(code)
        hist[key] = hist.get(key, 0) + 1
    return dict(sorted(hist.items(), key=lambda kv: int(kv[0])))


def peak_concurrency(par_dir: Path) -> int:
    events: list[tuple[float, int]] = []
    for par in par_dir.glob("*.par"):
        rec = parse_par_file(par)
        events.append((rec.start_epoch, 1))
        events.append((rec.end_epoch, -1))
    if not events:
        return 0
    events.sort(key=lambda t: (t[0], -t[1]))
    running = 0
    peak = 0
    for _ts, delta in events:
        running += delta
        peak = max(peak, running)
    return peak


def cpu_seconds_total(par_dir: Path, hz: int = USER_HZ) -> float:
    total = 0.0
    for par in par_dir.glob("*.par"):
        rec = parse_par_file(par)
        total += (rec.utime_jiffies + rec.stime_jiffies) / hz
    return total


def failed_exit_count(joblog: Path, par_dir: Path) -> int:
    pars = load_par_dir(par_dir)
    failed = 0
    for seq, _host, exitval, _cmd in parse_joblog_rows(joblog):
        code = authoritative_exit(exitval, pars.get(seq))
        if code != 0:
            failed += 1
    return failed


def job_count(joblog: Path) -> int:
    return len(parse_joblog_rows(joblog))


def par_file_count(par_dir: Path) -> int:
    return len(list(par_dir.glob("*.par")))


def make_synthetic_run(
    work_dir: Path,
    *,
    suffix: str,
    jobs: list[dict[str, object]],
) -> tuple[Path, Path]:
    """Build a unique joblog + par directory for anti-hardcoding tests."""
    work_dir.mkdir(parents=True, exist_ok=True)
    par_dir = work_dir / "par"
    par_dir.mkdir(exist_ok=True)
    joblog = work_dir / "joblog.tsv"
    header = "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand\n"
    lines = [header]
    for idx, spec in enumerate(jobs, start=1):
        seq = int(spec.get("seq", idx))
        host = str(spec.get("host", f"host-{suffix}"))
        start = float(spec["start_epoch"])
        end = float(spec["end_epoch"])
        runtime = end - start
        job_exit = int(spec.get("joblog_exit", spec.get("exit", 0)))
        par_exit = int(spec.get("exit", job_exit))
        slot = int(spec["slot"])
        ut = int(spec.get("utime_jiffies", 50 + seq))
        st = int(spec.get("stime_jiffies", 10))
        cmd = str(spec.get("command", f"task-{suffix}-{seq}"))
        lines.append(
            f"{seq}\t{host}\t{start:.3f}\t{runtime:.3f}\t0\t0\t{job_exit}\t0\t{cmd}\n"
        )
        par_path = par_dir / f"job-{seq:04d}-{suffix}.par"
        par_path.write_text(
            "\n".join(
                [
                    f"seq={seq}",
                    f"slot={slot}",
                    f"exit={par_exit}",
                    f"utime_jiffies={ut}",
                    f"stime_jiffies={st}",
                    f"wall_sec={runtime:.3f}",
                    f"start_epoch={start:.3f}",
                    f"end_epoch={end:.3f}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    joblog.write_text("".join(lines), encoding="utf-8")
    return joblog, par_dir


def db_job_count(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])
    finally:
        conn.close()


def db_distinct_seq_count(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute("SELECT COUNT(DISTINCT seq) FROM jobs").fetchone()[0])
    finally:
        conn.close()
