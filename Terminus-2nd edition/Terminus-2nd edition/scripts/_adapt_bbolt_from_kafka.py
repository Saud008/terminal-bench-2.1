#!/usr/bin/env python3
"""Adapt kafka-segment template -> bbolt-bucket-tx-snapshot-exporter."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "bbolt-bucket-tx-snapshot-exporter"

REPLS = [
    ("kafka-segment-offset-compaction-exporter", "bbolt-bucket-tx-snapshot-exporter"),
    ("github.com/terminus/kseg", "github.com/terminus/bbolt"),
    ("kseg", "bbolt"),
    ("segment-manifest.json", "bbolt-bbolt-bbucket-manifest.json"),
    ("segment-export-report.json", "bbolt-publish-report.json"),
    ("segment.header.json", "bucket.header.json"),
    ("replay.segment.jsonl", "replay.bucket.jsonl"),
    ("reference_segment", "reference_bucket"),
    ("replay_segment", "replay_bucket"),
    ("snapshot_offset", "snapshot_tx_id"),
    ("final_offset", "final_tx_id"),
    ("initial_sequence", "initial_checksum"),
    ("partition_id", "bucket_name"),
    ("PartitionID", "BucketName"),
    ("exported_at_offset", "exported_at_tx_id"),
    ("ExportedAtOffset", "ExportedAtTxID"),
    ("epoch_bump", "tx_id_reset"),
    ("EpochBump", "TxIDReset"),
    ("txn_open", "tx_begin"),
    ("TxnOpen", "TxBegin"),
    ("txn_commit", "tx_commit"),
    ("TxnCommit", "TxCommit"),
    ("RecordTxnOpen", "OpTxBegin"),
    ("RecordTxnCommit", "OpTxCommit"),
    ("RecordEpochBump", "OpTxIDReset"),
    ("RecordPut", "OpPut"),
    ("RecordTombstone", "OpDelete"),
    ("tombstone", "delete"),
    ("Tombstone", "Delete"),
    ("SegmentLine", "BucketLine"),
    ("segment-format.md", "bucket-format.md"),
    ("snapshot-barrier.md", "tx-snapshot-barrier.md"),
    ("commit-semantics.md", "tx-commit-semantics.md"),
    ("Kafka-style", "BBolt-style"),
    ("Kafka ", "BBolt "),
    ("kafka ", "bbolt "),
    ("compacted segment", "bucket tx"),
    ("segment line", "bucket record"),
    ("segment replay", "bucket replay"),
    ("segment ", "bucket "),
    ("Segment ", "Bucket "),
    ("internal/segment", "internal/bucket"),
    ("package segment", "package bucket"),
    ("offset.go", "txid.go"),
    ("OnEpochBump", "OnTxIDReset"),
    ("AdvanceChecksumSequence", "AdvanceChecksum"),
    ("ChecksumSequence", "ChecksumCursor"),
    ("ResolveFinalOffset", "ResolveFinalTxID"),
    ("FinalOffset", "FinalTxID"),
    ("SnapshotOffset", "SnapshotTxID"),
    ("record_offset", "record_tx"),
    ("recordOffset", "recordTx"),
    ("line.Offset", "line.TxID"),
    ('"offset"', '"tx_id"'),
    ("Offset   int", "TxID     int"),
    ("Offset int", "TxID int"),
    ("compact.go", "apply.go"),
    ("internal/store/compact", "internal/store/apply"),
    ("store/compact", "store/apply"),
    ("ApplyTombstone", "ApplyDelete"),
    ("TxnOpen", "TxBegin"),
    ("compact.go", "apply.go"),
    ("parse.go", "parse_bucket.go"),
    ("101-epoch-bump-trap", "101-tx-id-reset-trap"),
    ("epoch-bump", "tx-id-reset"),
    ("epoch bump", "tx_id_reset"),
    ("epoch_bump", "tx_id_reset"),
    ("002-txn-tombstone", "002-txn-delete"),
    ("txn-tombstone", "txn-delete"),
    ("tombstone compaction", "prefix delete compaction"),
    ("epoch_bump_trap", "tx_id_reset_trap"),
    ("hidden_epoch_bump", "hidden_tx_id_reset"),
    ("test_txn_tombstone", "test_txn_prefix_delete"),
    ("004-pending-txn-overlay", "004-pending-tx-overlay"),
]


def transform_text(text: str) -> str:
    for a, b in REPLS:
        text = text.replace(a, b)
    return text


def main() -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {
            ".go", ".md", ".py", ".sh", ".toml", ".json", ".jsonl", ".mod", ".dockerignore",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = transform_text(text)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")

    renames: list[tuple[Path, Path]] = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if "segment" in path.name and "bucket" not in path.name:
            renames.append((path, path.with_name(path.name.replace("segment", "bucket"))))
        if path.name == "offset.go":
            renames.append((path, path.with_name("txid.go")))
        if path.name == "compact.go":
            renames.append((path, path.with_name("apply.go")))
        if path.name == "parse.go" and "bucket" in str(path):
            renames.append((path, path.with_name("parse_bucket.go")))
    for old, new in renames:
        if old.exists() and old != new:
            new.parent.mkdir(parents=True, exist_ok=True)
            if new.exists():
                shutil.rmtree(new) if new.is_dir() else new.unlink()
            old.rename(new)

    seg = ROOT / "environment" / "internal" / "segment"
    bkt = ROOT / "environment" / "internal" / "bucket"
    if seg.exists() and not bkt.exists():
        seg.rename(bkt)

    print("ok", ROOT)


if __name__ == "__main__":
    main()
