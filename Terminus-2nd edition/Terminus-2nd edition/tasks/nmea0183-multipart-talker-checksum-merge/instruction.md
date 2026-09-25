The marine telemetry team needs the NMEA0183 merge utility under /app (nmeapipeline merge) to publish structured merge reports from GPS sentence streams. Implement the ingest-to-staging-to-export pipeline so streams under /app/fixtures/streams/ produce /app/output/merge-report.json that satisfies /app/docs/merge-contract.md, /app/docs/report-schema.md, and /app/docs/merge-snapshot.md.

Ingest composition runs in merge/compose.rs with fragment assembly in merge/multipart.rs, session replay reconciliation in session/reconcile.rs, and cross-run buffering in session/pending.rs. Export reads /app/state/merge-snapshot.json through export/staging.rs, validates the snapshot in export/validate.rs, finalizes digests in export/writer.rs, and assembles the report in export/wrap.rs. The merge/accumulate.rs helper is legacy and not on the hot path.

Multi-chunk replay uses --state /app/state/merge-session.json so incomplete multipart groups and RMC date context survive across successive inputs. Session replay rules for pending merge, orphan drops, stale pending recovery, and duplicate fragment resolution are defined only in /app/docs/merge-contract.md. Export must publish from the snapshot artifact, not by re-parsing the input stream.

Preserve existing module paths and public function signatures in the Rust sources under /app/crates/nmeapipeline/src/. The verifier replays golden module sources during partial-fix probes; change implementation bodies only. If you must alter a public API, update every module that depends on it in the same build.

The Rust toolchain is available offline under /usr/local/cargo/bin.
