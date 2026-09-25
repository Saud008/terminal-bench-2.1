# CLI surface

Binary: /app/bin/wfhistctl

| Verb | Flags | Outputs |
|------|-------|---------|
| ingest-history | --namespace, --scenario, optional --fixture-dir | /app/state/wf-history-staging.json |
| compact-summary | --namespace, --scenario | /app/work/wf-compaction-audit.json, /app/state/wf-compaction-seal.json |
| emit-inspect | --namespace, --scenario, optional --output-db, --output-risk | /app/output/inspection.db, /app/output/replay-risk-report.jsonl |

Fixed verb order for full inspector runs: ingest-history then compact-summary then emit-inspect.
