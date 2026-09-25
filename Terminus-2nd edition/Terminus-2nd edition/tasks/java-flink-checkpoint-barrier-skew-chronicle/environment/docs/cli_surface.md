# flink-skew CLI surface

Binary path: /app/bin/flink-skew.jar

Invocation pattern:

java -jar /app/bin/flink-skew.jar <verb> [flags]

## load-events

```
load-events --input DIR --out PATH
```

Reads all .jsonl files under DIR in lexicographic order, deduplicates per load-events-idempotency.md, writes event_index.json to PATH.

## align-barriers

```
align-barriers --index PATH --out PATH
```

Reads event_index.json, applies operator mapping, watermark guard, chain boundary rules, writes alignment.buffer JSONL to PATH.

## emit-chronicle

```
emit-chronicle --buffer PATH --out PATH
```

Reads alignment.buffer, computes per-checkpoint operator skew rows, writes barrier_skew_chronicle.json to PATH.
