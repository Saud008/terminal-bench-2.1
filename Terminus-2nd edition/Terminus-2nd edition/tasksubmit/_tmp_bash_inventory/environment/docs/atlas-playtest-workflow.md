# Pipeline overview

hostsatlas is a two-stage auditor for Ansible inventory trees.

Ingest reads a tree manifest, walks the inventory root, records merge order from hosts.ini sections, merges group lineage, resolves group_vars and host_vars precedence, detects vault markers and plaintext secret keys, applies ignore patterns, and writes /app/state/host-rows.ndjson, /app/state/atlas-rows.ndjson, and /app/state/scan-manifest.json.

Export reads staging artifacts only and writes hosts-atlas-report.json under /app/output. Export must not reopen inventory paths from the manifest.

scan-manifest.json stores staging_digest. That digest is sha256 over the exact bytes of host-rows.ndjson followed by the exact bytes of atlas-rows.ndjson. Each staged file is UTF-8 NDJSON with one sorted-key JSON object per line and a trailing newline after the final row.

Cross-run state lives in run-seq.json keyed by tree fingerprint.
