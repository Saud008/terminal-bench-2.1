# CLI surface

vcreplay exposes three subcommands in fixed verb order for a full audit run.

## load

```text
vcreplay load --room ROOM --scenario SCENARIO [--fixture-dir DIR]
```

Reads shard files from DIR/rooms/SCENARIO/shards/ in numeric sequence order. Writes /app/state/chat-staging.json

## reconcile

```text
vcreplay reconcile --room ROOM --scenario SCENARIO
```

Reads chat-staging.json. Writes /app/work/reconcile-findings.json and increments reconcile_revision in /app/state/reconcile-revision.json

## emit-timeline

```text
vcreplay emit-timeline --room ROOM --scenario SCENARIO --output PATH
```

Refuses when reconcile_revision is zero. Writes audit timeline JSONL to PATH.

Default output when --output is omitted: /app/output/audit-timeline.jsonl
