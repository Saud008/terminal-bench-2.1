# CLI surface

archctl at /usr/local/bin/archctl reads /app/config/queue.json unless --config is passed.

Subcommands:

seed — load a scenario JSONL into the SQLite queue.
  archctl seed --seed SEED --scenario NAME
  Scenario files live under /app/fixtures/scenarios/NAME.jsonl.

archive — snapshot pending tasks, write gzip bundle + index sidecar.
  archctl archive --seed SEED --scenario NAME
  Writes /app/work/archives/SEED-NAME.bundle and SEED-NAME.idx.json.
  Also writes /app/state/archive-snapshot.json listing canonical task order.

restore — import archived tasks back into the queue from bundle + index.
  archctl restore --seed SEED --scenario NAME

purge — delete archived rows older than a UTC cutoff timestamp.
  archctl purge --before RFC3339

manifest — export restore manifest JSON after restore.
  archctl manifest --seed SEED --scenario NAME --output PATH

All subcommands exit non-zero on contract violation.
