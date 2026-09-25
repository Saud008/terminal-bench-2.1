#!/usr/bin/env python3
"""One-off adapter: leveldb template -> bbolt-bucket-tx-snapshot-exporter."""
from __future__ import annotations

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
    ("BatchLine", "BucketLine"),
    ("OpBatchCommit", "OpTxCommit"),
    ("OpSequenceReset", "OpTxIDReset"),
    ("AdvanceChecksumSequence", "AdvanceChecksum"),
    ("ChecksumSequence", "ChecksumCursor"),
    ("ExportedAtSequence", "ExportedAtTxID"),
    ("exported_at_sequence", "exported_at_tx_id"),
    ("writebatch", "bbolt-bucket"),
    ("write-batch", "bucket-tx"),
    ("Write batch", "Bucket tx"),
    ("write batch", "bucket tx"),
    ("leveldb", "bbolt"),
    ("batch-format.md", "bucket-format.md"),
    ("internal/batch", "internal/bucket"),
    ("package batch", "package bucket"),
    ("parse_batch.go", "parse_bucket.go"),
    ("LoadLines", "LoadRecords"),
    ("batch_line", "bucket_record"),
    ('"sequence":', '"tx_id":'),
    ("line.Sequence", "line.TxID"),
    ("recordSeq", "recordTx"),
    ("snapshotSeq", "snapshotTx"),
    ("NewReplayState(snapshotSeq", "NewReplayState(snapshotTx"),
    ("Sequence int", "TxID int"),
    ("sequence {record_seq}", "tx_id {record_tx}"),
    ("sequence {recordSeq}", "tx_id {recordTx}"),
    ("record_seq", "record_tx"),
    ("recordSeq", "recordTx"),
    ("snapshot_barrier", "snapshot_barrier"),
    ("barrier/sequence.go", "barrier/txid.go"),
    ("sequence.go", "txid.go"),
]


TEXT_SUFFIX = {
    ".go", ".md", ".py", ".sh", ".toml", ".json", ".jsonl", ".mod", ".dockerignore", ".txt",
}


def main() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIX:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        orig = text
        for a, b in REPLS:
            text = text.replace(a, b)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")

  # rename paths containing batch -> bucket
    renames: list[tuple[Path, Path]] = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        name = path.name
        if "batch" in name and "bucket" not in name:
            new_name = name.replace("batch", "bucket").replace("Batch", "Bucket")
            renames.append((path, path.with_name(new_name)))
        if path.name == "sequence.go" and "barrier" in str(path):
            renames.append((path, path.with_name("txid.go")))
    for old, new in renames:
        if old.exists() and old != new:
            new.parent.mkdir(parents=True, exist_ok=True)
            if new.exists():
                if new.is_dir():
                    shutil.rmtree(new)
                else:
                    new.unlink()
            old.rename(new)

    # rename internal/batch dir
    batch_dir = ROOT / "environment" / "internal" / "batch"
    bucket_dir = ROOT / "environment" / "internal" / "bucket"
    if batch_dir.exists() and not bucket_dir.exists():
        batch_dir.rename(bucket_dir)

    print("adapted", ROOT)


if __name__ == "__main__":
    main()
