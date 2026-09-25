The qwindex CLI under /app simulates split/merge index lifecycle for a search shard pipeline. Milestone 1 covers merge metadata cache invalidation, object store manifest UUID lineage, and checkpoint behavior when merge fails.

Repair merge, manifest, and checkpoint handling so they match /app/docs/merge-metadata.md, /app/docs/manifest-format.md, and /app/docs/checkpoint-rules.md. State files under /app/state/ include split-meta.json, manifest.json, merge-audit.json, and checkpoint.json.

Rebuild with cargo build --release --bin qwindex from /app. Subcommands are in /app/docs/cli.md. When TB3_DOCS_DIR is set to an absolute directory, index --batch accepts files from that directory the same as /app/fixtures/docs/. Do not edit /app/docs/, /app/fixtures/, or /opt/verifier-fixtures/.
