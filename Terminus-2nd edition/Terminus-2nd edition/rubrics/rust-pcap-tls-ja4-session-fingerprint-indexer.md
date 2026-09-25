# Platform rubric — rust-pcap-tls-ja4-session-fingerprint-indexer

**Task folder:** tasks/rust-pcap-tls-ja4-session-fingerprint-indexer/

Agent parses CAPS capsule framing and five-tuple session quads from binary captures, +3
Agent reassembles fragmented TLS records before ClientHello parsing, +3
Agent assigns client and server roles from first client-direction frame per session, +2
Agent canonicalizes JA4 strings with sorted cipher and extension lists, +3
Agent deduplicates retransmitted frames by sequence and payload hash, +2
Agent counts fragment_gap and retransmit anomalies per session during ingest, +2
Agent writes sorted JSONL staging rows with handshake material before export, +2
Agent exports session_index.json with totals matching session list length, +2
Agent honors TB3_CAPSULE_DIR override for alternate capsule directories, +2
Agent rebuilds ja4idx release binary before each ingest export subprocess, +2
Agent patches decoy_telemetry crate expecting export output changes, -3
Agent hardcodes session_index.json without running ja4idx export, -5
Agent fixes JA4 canonicalization only while leaving retransmit dedupe broken, -3
Agent sorts sessions by frame count instead of session_id hex order, -2
Agent reads bundled fixtures when TB3_CAPSULE_DIR points elsewhere, -3
