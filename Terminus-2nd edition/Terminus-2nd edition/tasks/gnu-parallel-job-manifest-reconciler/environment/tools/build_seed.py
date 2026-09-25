#!/usr/bin/env python3
"""Build bundled seed joblog + .par fixtures for the image."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def write_par(path: Path, **fields: str | int | float) -> None:
    lines = [f"{k}={v}" for k, v in fields.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_seed(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    par_dir = dest / "par"
    par_dir.mkdir(exist_ok=True)

    joblog = dest / "joblog.tsv"
    joblog.write_text(
        "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand\n"
        "1\tbuild01\t1700000001.000\t0.40\t0\t0\t0\t0\tsleep 0.1\n"
        "2\tbuild01\t1700000001.050\t0.35\t0\t0\t0\t0\techo ok\n"
        "3\tbuild01\t1700000002.000\t0.50\t0\t0\t0\t0\tmake all\n"
        "4\tbuild01\t1700000002.100\t0.20\t0\t0\t127\t0\tmissing-cmd\n",
        encoding="utf-8",
    )

    write_par(
        par_dir / "job-0001.par",
        seq=1,
        slot=1,
        exit=0,
        utime_jiffies=80,
        stime_jiffies=20,
        wall_sec=0.38,
        start_epoch=1700000001.000,
        end_epoch=1700000001.380,
    )
    write_par(
        par_dir / "job-0002.par",
        seq=2,
        slot=2,
        exit=0,
        utime_jiffies=60,
        stime_jiffies=15,
        wall_sec=0.33,
        start_epoch=1700000001.050,
        end_epoch=1700000001.380,
    )
    write_par(
        par_dir / "job-0003.par",
        seq=3,
        slot=1,
        exit=0,
        utime_jiffies=120,
        stime_jiffies=30,
        wall_sec=0.48,
        start_epoch=1700000002.000,
        end_epoch=1700000002.480,
    )
    write_par(
        par_dir / "job-0004.par",
        seq=4,
        slot=3,
        exit=127,
        utime_jiffies=10,
        stime_jiffies=5,
        wall_sec=0.18,
        start_epoch=1700000002.100,
        end_epoch=1700000002.280,
    )


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/fixtures/seed")
    if out.exists():
        shutil.rmtree(out)
    build_seed(out)


if __name__ == "__main__":
    main()
