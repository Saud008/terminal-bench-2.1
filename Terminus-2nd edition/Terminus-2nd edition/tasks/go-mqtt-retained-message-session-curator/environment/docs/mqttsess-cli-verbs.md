# CLI surface

Binary: /app/bin/mqttsessctl

| Verb | Flags | Outputs |
|------|-------|---------|
| ingest-journal | --broker, --scenario, optional --fixture-dir | /app/state/mqtt-journal-staging.json |
| merge-session | --broker, --scenario | /app/work/mqtt-merge-audit.json, /app/state/session-curator-seal.json |
| emit-atlas | --broker, --scenario, optional --output-atlas, --output-ledger | atlas jsonl + ledger jsonl |

Fixed verb order for full curator runs: ingest-journal then merge-session then emit-atlas.
