# CLI surface

The qwindex binary lives at /usr/local/bin/qwindex after cargo build --release --bin qwindex from /app.

Subcommands:

index --batch PATH --state DIR loads JSONL documents into the pending split buffer. Each line has doc_id (integer) and body (string).

split-publish --state DIR materializes the pending buffer into a published split, updates /app/state/manifest.json, and writes /app/state/split-meta.json.

delete --query TOKEN --state DIR records a delete-by-query tombstone for TOKEN. Writes /app/state/delete-audit.json.

merge --left SPLIT_ID --right SPLIT_ID --state DIR merges two published splits. Writes /app/state/merge-audit.json and updates checkpoint per /app/docs/checkpoint-rules.md.

search --query TOKEN --state DIR --report PATH runs a token search and writes JSON with query, hit_count, and matching doc_ids sorted ascending.

Default database path is /app/data/qwindex.db. When TB3_DOCS_DIR is set to an absolute directory, index --batch accepts files from that directory the same as /app/fixtures/docs/.
