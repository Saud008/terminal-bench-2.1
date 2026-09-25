# qqraftctl

Host-local quorum membership ops control plane for offline OCF Raft WAL and snapshot bundles. Admit → stage → audit → sealed export. No live broker.

- Binary: `/app/bin/qqraftctl`
- Ops contracts: `/app/docs/`
- Witness head: `/app/state/raft-staging.json`
- Membership audit: `/app/work/replica-membership-report.json`
- Sealed outputs: `/app/output/committed-queue-state.jsonl` and `/app/output/quorum-ledger-seal.json`

Quorum-cluster operators use `replay-log`, `merge-snapshot`, `audit-membership`, and `export-committed` to admit voter epochs and refuse uncommitted tails before sealing.
