# Submission explanations — ros2-bag-qos-gap-fill-deadline-export

**Task folder:** tasks/ros2-bag-qos-gap-fill-deadline-export/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must repair four Rust modules in the bag-audit CLI so replayed rosbag2 bundles export correct SQLite rows through ingest, per-topic gap fill, QoS deadline scanning, and export. Contracts are split across /app/docs/bag-format.md, gap-fill-rules.md, qos-deadline.md, and export-schema.md, so fixing one stage is not enough. The broken read path decodes legacy payloads using the remapped topic instead of the raw JSONL topic. Gap fill drops neighbor payload inheritance and ignores the seed nanosecond adjustment. Deadline logic multiplies by speed, reads receive_ns instead of publish_ns, and skips the effective threshold formula. SQLite export hardcodes synthetic to zero. Partial-fix traps prove read-only, gap-only, deadline-only, or sqlite-only repairs still fail dedicated bags such as remap-legacy, gap-dense, speed-factor, and twin-deadline.

## Solution Explanation

The oracle replaces bag/read.rs, bag/gap.rs, qos/deadline.rs, and export/sqlite.rs with golden implementations, then rebuilds bag-audit with cargo build --release and installs the binary. load_bag must decode payload bytes from the raw topic before applying metadata remap to the canonical topic string. fill_gaps inserts synthetic rows with linear publish_ns interpolation, lower-neighbor payload copy, receive_ns equal to publish_ns, and a (seed mod 11) nanosecond bump while preserving per-topic monotonicity. find_deadline_misses computes effective_deadline_ms as max(1, ceil(deadline_ms / speed) - (seed mod 5)), compares consecutive publish_ns spacing per canonical topic, and stores configured deadline_ms in miss rows. write_export writes SHA-256 payload hashes and sets synthetic to 1 for gap-filled messages.

## Verification Explanation

test.sh runs cargo build --release before pytest so every test exercises a freshly compiled CLI. Tests invoke /usr/local/bin/bag-audit audit as a subprocess across all eleven catalog bags and four seeds, comparing SQLite messages and deadline_misses tables to an independent Python reference in reference_audit.py. Integration tests cover speed-factor replay thresholds, seed-ladder miss variation, multi-topic gap isolation, payload-chain inheritance, and combo-stack remap composition. TestPartialFixTraps installs golden modules except one broken file and asserts trap bags still diverge from the reference, blocking one-file shortcuts. Rebuild and golden-module matrix tests confirm the full pipeline after source reset.
