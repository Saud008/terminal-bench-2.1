#!/usr/bin/env python3
"""Leveldb template -> bbolt-bucket-tx-snapshot-exporter (careful rename)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "bbolt-bucket-tx-snapshot-exporter"

REPLS = [
    ("leveldb-writebatch-sequence-manifest", "bbolt-bucket-tx-snapshot-exporter"),
    ("github.com/terminus/wbatch", "github.com/terminus/bbolt"),
    ("wbatch", "bbolt"),
    ("batch-manifest.json", "bbolt-bbolt-bbucket-manifest.json"),
    ("batch-export-report.json", "bbolt-publish-report.json"),
    ("db.header.json", "bucket.header.json"),
    ("replay.batch.jsonl", "replay.bucket.jsonl"),
    ("reference_batch", "reference_bucket"),
    ("replay_batch", "replay_bucket"),
    ("snapshot_sequence", "snapshot_tx_id"),
    ("final_sequence", "final_tx_id"),
    ("initial_sequence", "initial_checksum"),
    ("sequence_reset", "tx_id_reset"),
    ("batch_commit", "tx_commit"),
    ("OpBatchCommit", "OpTxCommit"),
    ("OpSequenceReset", "OpTxIDReset"),
    ("BatchLine", "BucketLine"),
    ("line.Sequence", "line.TxID"),
    ("SnapshotSequence", "SnapshotTxID"),
    ("FinalSequence", "FinalTxID"),
    ("InitialSequence", "InitialChecksum"),
    ("AdvanceChecksumSequence", "AdvanceChecksum"),
    ("OnSequenceReset", "OnTxIDReset"),
    ("ResolveFinalSequence", "ResolveFinalTxID"),
    ("ExportedAtSequence", "ExportedAtTxID"),
    ("exported_at_sequence", "exported_at_tx_id"),
    ("recordSeq", "recordTx"),
    ("record_seq", "record_tx"),
    ("snapshotSeq", "snapshotTx"),
    ("snapshot_seq", "snapshot_tx"),
    ("NewReplayState(snapshotSeq", "NewReplayState(snapshotTx"),
    ("NoteApplied(recordSeq", "NoteApplied(recordTx"),
    ("Within(recordSeq", "Within(recordTx"),
    ("LoadLines", "LoadRecords"),
    ("batch-format.md", "bucket-format.md"),
    ("write-batch", "bucket-tx"),
    ("write batch", "bucket tx"),
    ("Write batch", "Bucket tx"),
    ("writebatch", "bbolt-bucket"),
    ("leveldb", "bbolt"),
    ("internal/batch", "internal/bucket"),
    ("package batch", "package bucket"),
    ("parse_batch.go", "parse_bucket.go"),
    ("barrier/sequence.go", "barrier/txid.go"),
    ('json:"sequence"', 'json:"tx_id"'),
    ('"sequence":', '"tx_id":'),
    ("Sequence int", "TxID int"),
    ("101-sequence-reset-trap", "101-tx-id-reset-trap"),
    ("sequence-reset", "tx-id-reset"),
    ("sequence reset", "tx_id_reset"),
]


def main() -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in {
            ".go", ".md", ".py", ".sh", ".toml", ".json", ".jsonl", ".mod", ".dockerignore",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for a, b in REPLS:
            text = text.replace(a, b)
        path.write_text(text, encoding="utf-8", newline="\n")

    renames: list[tuple[Path, Path]] = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if "batch" in path.name and "bucket" not in path.name:
            renames.append((path, path.with_name(path.name.replace("batch", "bucket"))))
        if path.name == "sequence.go":
            renames.append((path, path.with_name("txid.go")))
    for old, new in renames:
        if old.exists() and old != new:
            new.parent.mkdir(parents=True, exist_ok=True)
            if new.exists():
                shutil.rmtree(new) if new.is_dir() else new.unlink()
            old.rename(new)

    batch_dir = ROOT / "environment" / "internal" / "batch"
    bucket_dir = ROOT / "environment" / "internal" / "bucket"
    if batch_dir.exists():
        if bucket_dir.exists():
            shutil.rmtree(bucket_dir)
        batch_dir.rename(bucket_dir)

    print("renamed", ROOT)


if __name__ == "__main__":
    main()
