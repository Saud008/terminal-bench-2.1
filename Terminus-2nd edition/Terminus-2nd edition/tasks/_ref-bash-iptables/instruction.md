Implement the fw-risk-map semantic translation risk mapper. The CLI lives at /app/scripts/fw-risk-map (also installed as /usr/local/bin/fw-risk-map). The tool compares iptables-save snapshots with nftables ruleset excerpts and emits a structured risk report describing semantic drift between legacy iptables rules and their nftables translations.

Stage ingest loads a pair manifest, parses both sides with AWK normalizers, computes policy precedence ranks, binds per-rule counters, scans for unsupported iptables match modules, and writes staged NDJSON tuples plus /app/state/staging-meta.json. Stage export reads staging artifacts only and produces /app/output/translation-risk-report.json with findings grouped by chain policy precedence, match extension normalization gaps, counter preservation mismatch, rule ordering divergence, and unsupported feature records. Severity weights in /app/config/severity-weights.json mirror /app/docs/risk-report-schema.md.

Contracts live in /app/docs/pipeline-overview.md, /app/docs/staging-schema.md, /app/docs/risk-report-schema.md, /app/docs/match-normalization.md, /app/docs/policy-precedence.md, and /app/docs/unsupported-features.md. Export must never reopen the iptables or nft paths from the pair manifest after ingest completes.

Cross-run behavior tracks /app/state/run-seq.json and pair fingerprints. Re-ingesting an unchanged pair must keep run_seq stable and reproduce identical staging_digest values.

/app/decoy/xtables-translate.sh and /app/wrap/nft_compat_legacy.awk are legacy utilities outside the fw-risk-map hot path.

Hidden verifier pairs live under /opt/verifier-fixtures/tb3-pairs/ for match normalization and unsupported module traps.

Example:

/app/scripts/reset-state.sh
/app/scripts/fw-risk-map ingest --pair /opt/verifier-fixtures/tb3-pairs/match-trap/pair.json
/app/scripts/fw-risk-map export --pair tb3-match-trap --output /app/output/translation-risk-report.json
/app/scripts/fw-risk-map ingest --pair /app/fixtures/pairs/simple-accept/pair.json
/app/scripts/fw-risk-map export --pair simple-accept --output /app/output/translation-risk-report.json

Exit 0 on success. Exit 2 when ingest cannot read the pair manifest. Exit 3 when export runs before a matching ingest snapshot exists.

Do not edit /app/docs/, /app/fixtures/, /app/config/, or files under /tests/.
