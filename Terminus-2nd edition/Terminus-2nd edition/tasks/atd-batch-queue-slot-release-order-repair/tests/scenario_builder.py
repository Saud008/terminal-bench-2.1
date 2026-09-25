"""Build hidden scenario fixtures for atd verifier."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def build_hidden_slot_trap(dest: Path) -> Path:
    """Hidden scenario: occupied letter a forces retry to b."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (dest / "scripts").mkdir()
    (dest / "scripts" / "worker.sh").write_text("#!/bin/sh\necho hidden\n", encoding="utf-8")
    (dest / "preexisting_spool").mkdir()
    (dest / "preexisting_spool" / "a0000000001").write_text(
        "ATQ_EPOCH=1699999990 BATCH=ghost JOB=blocker\n#!/bin/sh\necho block\n",
        encoding="utf-8",
    )
    conf = {
        "system_timezone": "UTC",
        "batches": [
            {
                "batch_id": "hidden",
                "jobs": [
                    {
                        "job_id": "trap",
                        "atq_epoch": 1700000000,
                        "script": "worker.sh",
                        "start_letter": "a",
                        "umask": "0022",
                        "exit_code": 0,
                    }
                ],
            }
        ],
    }
    (dest / "scenario.conf.json").write_text(json.dumps(conf, indent=2) + "\n", encoding="utf-8")
    return dest


def build_crash_seq_fixture(dest: Path) -> Path:
    """Fixture with partial .SEQ body to test atomic read recovery."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (dest / "scripts").mkdir()
    (dest / "scripts" / "worker.sh").write_text("#!/bin/sh\necho seq\n", encoding="utf-8")
    (dest / "partial_seq").write_text("99\n", encoding="utf-8")
    conf = {
        "system_timezone": "UTC",
        "batches": [
            {
                "batch_id": "seq",
                "jobs": [
                    {
                        "job_id": "once",
                        "atq_epoch": 1700000000,
                        "script": "worker.sh",
                        "start_letter": "f",
                        "umask": "0022",
                        "exit_code": 0,
                    }
                ],
            }
        ],
    }
    (dest / "scenario.conf.json").write_text(json.dumps(conf, indent=2) + "\n", encoding="utf-8")
    return dest
