Task identity c8f2e41b defines the engineering problem for rust rosbag topic clock skew indexer. See /app/docs/engineering-problem-contract.md for scope boundaries.

        Mobile robotics calibration teams playback simplified rosbag metadata and multi-topic message streams to publish a numerical clock skew atlas before fleet deployment. Build skew-cal on the working Rust baseline under /app following the calibration state lattice in /app/docs/rosbag-calibration-lattice.md: warmup latch manifests, normalize sensor header timelines, seal median-anchor sync windows around a reference topic clock, and emit per-sensor drift metrics with least-squares correlation as deterministic JSON under /app/output/.

Install skew-cal at /app/bin/skew-cal with subcommands latch-meta, norm-stream, match-sync, and emit-skew. Manifest parsing, topic remapping, monotonic header stamp guards, median-anchor sync windows, duplicate msg index supersession, and least-squares drift slopes follow /app/docs/bag-manifest-schema.md, /app/docs/message-stream-format.md, /app/docs/monotonic-stamp-contract.md, /app/docs/sync-window-matching.md, /app/docs/duplicate-msg-index-policy.md, /app/docs/stream-gap-ledger.md, /app/docs/drift-regression-contract.md, /app/docs/skew-atlas-fields.md, /app/docs/manifest-latch-schema.md, /app/docs/timeline-ledger-schema.md, /app/docs/sync-lattice-schema.md, /app/docs/fixture-bag-catalog.md, /app/docs/rosbag-calibration-lattice.md, and /app/docs/pytest-verifier-primitives.md.

skew-cal latch-meta reads bag_meta.json and writes /app/state/manifest-latch/<bag-id>.json with manifest_revision tracking.

skew-cal norm-stream reads messages.jsonl, applies remap rules, enforces monotonic header stamps, resolves duplicate msg indices by relay_pass, and writes /app/work/timeline-ledger/<bag-id>.jsonl.

skew-cal match-sync reads staged messages and the manifest latch file, builds median-anchor synchronization windows around the reference topic, and writes /app/work/sync-lattice/<bag-id>.jsonl.

skew-cal emit-skew reads sync windows, computes per-topic drift slopes and intercepts against the reference timeline, aggregates drop counts from stream gaps, and writes skew atlas JSON to the caller --output path ending with -skew-atlas.json.

        Bundled rover field logs live under /app/fixtures/bags/ per /app/docs/fixture-bag-catalog.md. Runtime bag roots honor TB3_BAG_ROOT. Reference topic and sync window overrides honor TB3_REFERENCE_TOPIC and TB3_SYNC_WINDOW_NS. Manifest latch artifacts persist under /app/state/manifest-latch/ and skew atlas JSON under /app/output/.

Compile skew-cal with cargo build --release --locked from /app and install the binary to /app/bin/skew-cal. Run /app/scripts/reset-workspace.sh before cross-run verifier cases. The tf extrapolation decoy module is not used by latch-meta, norm-stream, match-sync, or emit-skew.


Verifier harness modules tests/conftest.py and tests/temporal_sync_oracle.py implement independent reference recomputation; hashlib digests follow /app/docs/pytest-verifier-primitives.md and /app/tools/audit_digest_ref.py.
