# Rosbag calibration state lattice

Mobile robotics field-log calibration follows a four-state lattice distinct from color-management bundlers or MIDI quantizers.

Warmup latch: latch-meta copies bag manifests into manifest-latch and assigns manifest_revision counters per bag id.

Timeline normalization: norm-stream remaps raw sensor topics, collapses duplicate msg indices by relay_pass, and enforces strict monotonic header_stamp_ns per topic.

Sync lattice seal: match-sync builds median-anchor windows around the reference topic clock and records paired sensor headers inside sync-lattice JSONL.

Skew atlas publish: emit-skew fits per-topic clock skew slopes against the reference timeline and writes deterministic skew atlas JSON with audit_digest.

Domain terms: rosbag field-log playback, sensor header timeline, clock skew correlation, median-anchor pairing, multi-topic temporal alignment, fleet calibration playback.
