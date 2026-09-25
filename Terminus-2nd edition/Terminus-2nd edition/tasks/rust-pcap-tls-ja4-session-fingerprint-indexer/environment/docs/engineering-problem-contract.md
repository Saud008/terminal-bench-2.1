# Engineering problem contract — rust-pcap-tls-ja4-session-fingerprint-indexer

This task is about reconstructing rerunnable TLS session evidence from capsule captures, not about patching one report field. The engineering identity is a two-stage workflow in which intake must normalize packet-derived session state into a stable ledger and emit must derive a deterministic fingerprint index only from that ledger.

The core failure envelope is cross-stage disagreement. Partial fixes that only adjust JA4 formatting, only change dedupe, or only rewrite report sequence must still fail because the ledger would remain inconsistent with the emitted report. The product expects deterministic rerun across bundled capsules and alternate capsule directories, with identical session lexicographic order and repeatable output bytes after rebuild.

The persistence gate for this task is the session ledger at /app/state/session_ledger.jsonl, and emit must not bypass or recompute intake behavior from raw capsules. Rerun alignment depends on session lexicographic order, role assignment, retransmit filtering, and TLS record reconstruction remaining aligned across both stages.
