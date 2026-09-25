# CLI surface

Binary: mantidx

Subcommands:

- insert --batch PATH --state /app/state --db /app/data/mantidx.db
- delete --query TOKEN --state /app/state --db /app/data/mantidx.db
- rotate --state /app/state --db /app/data/mantidx.db
- merge-ram --left SEG --right SEG --state /app/state --db /app/data/mantidx.db
- update-attr --doc-id N --price N --state /app/state --db /app/data/mantidx.db
- search --query TOKEN --state /app/state --db /app/data/mantidx.db --report /app/state/search-report.json

When TB3_DOCS_DIR is set to an absolute directory, insert --batch accepts filenames from that directory the same as /app/fixtures/docs/.

State artifacts: rotate-meta.json, ram-segments.json, killlist.json, binlog-checkpoint.json, rotate-audit.json, merge-ram-audit.json, attribute-audit.json, search-report.json.
