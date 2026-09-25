# Platform rubric — loki-logql-label-filter-stage-pipeline

**Task folder:** tasks/loki-logql-label-filter-stage-pipeline/

Agent runs LogQL pipeline stages in documented order with matcher before json, +3
Agent keeps histogram unwrap _sum and _count labels while dropping le, +2
Agent applies line_format escape expansion before width unwrap, +2
Agent computes vector checksums using label insertion order not sorted keys, +3
Agent exports fingerprint from canonical query and staging snapshot only, +3
Agent fixes sum by parser to read grouped label names inside parentheses, +2
Agent rebuilds lokictl after editing internal pipeline packages, +2
Agent writes eval output to /app/state/logql-stage.json before export, +2
Agent ignores decoy wrap module on eval and export hot path, +1
Agent patches only ingest while leaving matcher stage order wrong, -3
Agent hashes raw query text instead of canonical fingerprint payload, -3
Agent promotes json fields into labels before matcher filtering, -2
Agent drops _sum or _count during histogram unwrap, -2
Agent uses sorted label keys for empty sum by checksum, -2
