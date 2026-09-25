Quorum-cluster operators run the host-local qqraftctl membership ops control plane at `/app/bin/qqraftctl`. Each offline ops pass admits OCF Raft WAL and snapshot bundles for a cluster scenario, stages a membership-bound witness head, enforces voter-epoch and commit-index gates, then publishes a sealed committed-queue ledger only when those gates hold. There is no live messaging broker or outbound network step. This is a system-administration host-local quorum membership ops control plane; keep add_voter / remove_voter epoch gates, leader handoff order, WAL-tail fences, snapshot `last_included_index` truncation, refusal to export uncommitted queue tail above `commit_index`, membership audit inventory, digest-bound `raft_seal`, and sealed ledger export aligned. It is not a generic service repair exercise.

Ops contracts under `/app/docs/`: `membership-trust-contract.md` for the ops objective; `cli-surface.md` for verb order and flags; `staging-pipeline.md` for admit → stage → audit → export order; `quorum-queue-raft-semantics.md` for quorum log replay semantics; `replica-membership-contract.md` for voter inventory and audit counts; `committed-export-schema.md` for sealed ledger schema and `raft_seal` binding; `leader-election-contract.md` for election application; `commit-index-contract.md` for commit fences; `term-index-ordering.md` and `wal-tail-fence-contract.md` for term/index order and queue-tail fences; `snapshot-bundle-schema.md` for truncation; `verifier-refmath-contract.md` for independent replay/export math. Canonical digests follow `/app/fixtures/digest_util.py`. The `--cluster` flag value is bound into staging and seal digests as-is.

Primary ops verbs:

```text
qqraftctl replay-log --cluster ID --scenario SLUG [--fixture-dir DIR]
qqraftctl merge-snapshot --cluster ID --scenario SLUG [--fixture-dir DIR]
qqraftctl audit-membership --cluster ID --scenario SLUG
qqraftctl export-committed --cluster ID --scenario SLUG [--output-ledger PATH] [--output-seal PATH]
```

`replay-log` writes `/app/state/raft-staging.json`. `merge-snapshot` applies truncation before membership audit when a snapshot exists. `audit-membership` writes the membership inventory report. `export-committed` may publish `/app/output/committed-queue-state.jsonl` and `/app/output/quorum-ledger-seal.json` (or `--output-ledger` / `--output-seal`) only after those gates hold. The telemetry decoy module is not on the replay, merge, or emit path.

Bundled scenarios live under `/app/fixtures/`. Off-catalog overlays under `/opt/verifier-fixtures/qqraftctl/` follow the same contracts. When `TB3_FIXTURE_DIR` is set, fixture roots may override for verifier-only overlays. After policy-module edits under `/app/internal/`, leave `/app/bin/qqraftctl` current. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
