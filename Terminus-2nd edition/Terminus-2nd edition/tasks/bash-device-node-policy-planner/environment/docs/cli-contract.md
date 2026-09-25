# CLI contract

Binary: /app/bin/udev-policy-planner

## ingest

```
udev-policy-planner ingest \
  --rules-dir RULES_DIR \
  --devices DEVICES_JSON \
  --modalias MODALIAS_TSV \
  --out STAGING_JSON
```

Exit 0 on success. Writes STAGING_JSON and updates /app/state/replay.seq when the staging digest changes.

## export

```
udev-policy-planner export \
  --staging STAGING_JSON \
  --policy POLICY_JSON \
  --out PLAN_JSON
```

Exit 0 on success. Reads STAGING_JSON from disk. Does not read RULES_DIR or DEVICES_JSON. Does not modify replay.seq.

## Global

- stderr lines starting with UDEVPLAN: are diagnostic only.
- All JSON outputs use UTF-8, LF newlines, trailing newline, sorted object keys at the top level.
