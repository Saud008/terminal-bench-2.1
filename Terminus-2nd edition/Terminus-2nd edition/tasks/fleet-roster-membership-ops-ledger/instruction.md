Fleet desk operators need a host-local rosterctl membership ops desk that keeps scenario-pack admission, voter inventory gates, posted-index fences, and sealed queue-ledger export aligned on one offline host. Operate `/app/bin/rosterctl` so admit → stage → audit → export follows the ops contracts under `/app/docs/`. There is no live broker and no outbound network. This is a system-administration host-local ops desk (admit → gate → seal), not a generic software engineering service-repair exercise.

Ops contracts under `/app/docs/` define the enforceable invariants:

- `/app/docs/membership-trust-contract.md` — ops objective and admission ladder
- `/app/docs/cli-surface.md` — verb order and flags
- `/app/docs/staging-pipeline.md` — admit → stage → audit → export order
- `/app/docs/roster-pack-semantics.md` — roster pack replay semantics
- `/app/docs/replica-membership-contract.md` — voter inventory and audit counts
- `/app/docs/committed-export-schema.md` — sealed ledger schema and seal binding
- `/app/docs/lead-claim-contract.md` — lead-claim application
- `/app/docs/posted-index-contract.md` — posted-index fence
- `/app/docs/epoch-index-ordering.md` and `/app/docs/posted-tail-fence-contract.md` — ordering and queue-tail fences
- `/app/docs/snapshot-bundle-schema.md` — truncation
- `/app/docs/roster-refmath-contract.md` — independent replay/export math

Canonical digests follow `/app/fixtures/digest_util.py`. The `--cluster` flag value is bound into staging and seal digests as-is.

Primary ops verbs:

```text
rosterctl replay-log --cluster ID --scenario SLUG [--fixture-dir DIR]
rosterctl merge-snapshot --cluster ID --scenario SLUG [--fixture-dir DIR]
rosterctl audit-membership --cluster ID --scenario SLUG
rosterctl export-committed --cluster ID --scenario SLUG [--output-ledger PATH] [--output-seal PATH]
```

`replay-log` writes `/app/state/membership-staging.json`. `merge-snapshot` applies snapshot truncation before membership audit when a snapshot exists. `audit-membership` writes the membership inventory report. `export-committed` may publish `/app/output/committed-queue-state.jsonl` and `/app/output/membership-seal.json` (or `--output-ledger` / `--output-seal`) only after those gates hold. Policy modules live under `/app/lib/roster/`; the decoy helper is not on the admit, gate, or emit path.

Bundled scenarios live under `/app/fixtures/`. Off-catalog overlays under `/opt/verifier-fixtures/rosterctl/` follow the same contracts. When `TB3_FIXTURE_DIR` is set, fixture roots may override for verifier-only overlays. After policy-module edits under `/app/lib/roster/`, leave `/app/bin/rosterctl` current. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
