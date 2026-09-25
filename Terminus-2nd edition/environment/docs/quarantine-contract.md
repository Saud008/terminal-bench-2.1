# Quarantine release contract

amavis-quarantine reconcile replays operator release requests for one scenario fixture. It is equivalent to prepare followed by commit.

```
amavis-quarantine reconcile --scenario <name> --seed <seed> --export <json>
amavis-quarantine prepare --scenario <name> --seed <seed>
amavis-quarantine commit --export <json>
```

## Spool layout

| Path | Role |
|------|------|
| /app/work/spool/spam/ | Spam-class quarantined messages |
| /app/work/spool/virus/ | Virus-class quarantined messages |
| /app/work/released/spam/ | Successfully released spam messages |
| /app/work/released/virus/ | Successfully released virus messages |

Each message is msg.QUARANTINE_ID.eml plus msg.QUARANTINE_ID.meta.json.

## Pipeline

1. Prepare: ingest scenario spool into /app/work/spool/ and write /app/state/spool-manifest.json per ingest contract.
2. Prepare: bump /app/state/release-epoch.json per /app/docs/epoch-schema.md.
3. Prepare: write /app/state/release-staging.json per /app/docs/release-staging.md (includes the bumped release_epoch and policy_digest from /app/docs/release-policy.md).
4. Prepare: initialize /app/work/ledger.json and session counters, clear custody journal, write /app/state/prepare-seal.json per /app/docs/custody-chain.md.
5. Commit: for each release row in the sealed requests.json (see seed ordering below), parse the amavis log line, enforce hold_token policy from /app/docs/release-policy.md, route to the correct queue directory, attempt release, update the ledger, and append custody receipts per /app/docs/custody-chain.md.
6. Commit: emit export JSON per /app/docs/export-schema.md.

## Seed ordering

For seed `alpha01`, process release rows in requests.json file order. For any other seed, sort rows by `sha256(seed + ":" + quarantine_id)` hex ascending before processing.

Duplicate release requests for an already-released quarantine id must be skipped without moving files or incrementing ledger sequence. Failed releases must not consume ledger sequence numbers.

Inter-module entry points are listed in /app/docs/module-api.md.
