# kcompactctl CLI surface

Fixed verb order: pull-segments, audit-log, publish-keys.

Binary path: /app/bin/kcompactctl

## pull-segments

kcompactctl pull-segments --topic TOPIC --scenario SCENARIO [--fixture-dir DIR]

Reads seg_NNN.jsonl segment files under DIR/compact-logs/SCENARIO/segments/ in numeric segment order.

## audit-log

kcompactctl audit-log --topic TOPIC --scenario SCENARIO

Writes /app/work/segment-audit-report.json and increments /app/state/compact-curator-seal.json.

Each finding entry in segment-audit-report.json requires fields: code, partition, offset, and detail.

## publish-keys

kcompactctl publish-keys --topic TOPIC --scenario SCENARIO [--output-snapshot PATH] [--output-lineage PATH]

Blocked when curator_seal is zero. Default outputs: /app/output/topic-key-snapshot.jsonl and /app/output/tombstone-lineage.jsonl.

internal/decoy is not authoritative for export.
