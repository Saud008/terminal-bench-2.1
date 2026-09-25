Host page-registry operators run the sledtool pagestore staging ops control plane on the local host. The plane admits offline batch JSONL packs, applies staging isolation barriers, publish seals, snapshot-pin compaction gates, crash-journal split_seq idempotency, page-registry checksum authenticity, and sealed range-export manifests. There is no remote cluster and no outbound network. This is a system-administration host-local ops control plane (batch → publish → seal); keep staging snapshots, pin files, and export manifests aligned across retries. It is not a generic Rust cargo rebuild, B-tree engine repair exercise, or pytest harness.

Ops contracts under `/app/docs/` define enforceable invariants:

- `/app/docs/tree-contract.md` — B-tree fanout, split mid, underflow preference, batch collapse order
- `/app/docs/staging-snapshot.md` — staging isolation and publish snapshot metrics
- `/app/docs/split-journal-order.md` — ParentPivot before RightPage split journal ordering
- `/app/docs/page-checksum.md` — FNV-1 page registry checksum including generation bytes
- `/app/docs/merge-high-key.md` — internal high_key bounds for scan-range pruning
- `/app/docs/compaction-pin-rules.md` — snapshot pin files block page reclaim
- `/app/docs/cli-reference.md` — sledtool verb surface and state paths

Primary ops verbs:

```text
sledtool batch --table NAME --input PATH
sledtool publish --table NAME
sledtool snapshot-pin --table NAME --snapshot-id ID
sledtool compact --table NAME
sledtool journal-replay --table NAME --journal PATH
sledtool scan-range --table NAME --start START --end END --out PATH
sledtool export --table NAME --out PATH
sledtool walk --table NAME
```

`sledtool batch` must write staging only and must not mutate committed export state. `sledtool publish` must commit staging and write `/app/state/sled-staging-snapshot.json`. `sledtool snapshot-pin` must record pinned page ids under `/app/state/pins/`. `sledtool compact` must leave pinned pages unreclaimed in `/app/state/page_registry.json`. `sledtool journal-replay` must apply crash journals idempotently on split_seq boundaries. `sledtool scan-range` must write sealed inclusive committed keys using correct internal-node high-key bounds.

Binary path: `/usr/local/bin/sledtool` (bash → `python3 -m sled.cli`). Policy modules live under `/app/lib/sled/`. Table names come from `--table`, or from `TB3_TABLE_PREFIX` when set to an absolute staging prefix. Bundled fixtures live under `/app/fixtures`. Hidden verifier overlays may appear under `/opt/verifier-fixtures/sled-journal`. After policy-module edits under `/app/lib/sled/`, leave `/usr/local/bin/sledtool` current (the verifier may invoke `/app/scripts/verifier-rebuild.sh`). Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
