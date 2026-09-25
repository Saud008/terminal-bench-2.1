Fleet desk operators need a host-local partyd occupancy ops desk that keeps invite admission, chained staging, sweep-epoch gates, and sealed audit export aligned on one offline host. Operate `/app/bin/partyd` so create → invite/accept/disconnect → sweep → export follows the ops contracts under `/app/docs/`. There is no HTTP listener and no outbound network. This is a system-administration host-local ops desk (admit → gate → seal), not a generic software engineering service-repair exercise.

Ops contracts under `/app/docs/` define the enforceable invariants:

- `/app/docs/audit-snapshot.md` — chained occupancy staging ledger
- `/app/docs/staging-digest.md` — canonical digest encoding
- `/app/docs/export-schema.md` — sealed audit export
- `/app/docs/sweep-contract.md` — sweep-epoch retirement gates
- `/app/docs/party-contract.md` — party lifecycle admission
- `/app/docs/invite-lifecycle.md` — invite acceptance
- `/app/docs/idempotency.md` — idempotent accept anti-replay
- `/app/docs/member-cap.md` — member-cap admission
- `/app/docs/fixture-catalog.md` — fixture inventory

Primary ops verbs:

```text
partyd create --leader ID [--max-members N] --mono-ms MS
partyd invite --party ID --invitee ID [--ttl-ms N] --mono-ms MS
partyd accept --invite ID --invitee ID --idempotency-key KEY --mono-ms MS
partyd disconnect --party ID --player ID --mono-ms MS
partyd sweep --mono-ms MS
partyd export --party ID --mono-ms MS
```

`create` admits a party into SQLite. `invite`, `accept`, and `disconnect` must stage chained checkpoints into `/app/state/party-audit-snapshot.json`. `sweep` expires invites, removes empty disbanded parties, advances and persists the sweep epoch, refreshes survivors, and retires vanished parties. `export` may publish `/app/output/party-audit.json` only from a verified staged entry. Conflict exits use code 2. Export refusals use code 3 and must not overwrite the export file.

Policy modules live under `/app/lib/party/`. The decoy helper is not on the admit, stage, sweep, or export path. Bundled fixtures live under `/app/fixtures/`. Hidden verifier seeds may appear under `/opt/verifier-fixtures`. After policy-module edits, leave `/app/bin/partyd` current. Do not edit `/app/docs/`, `/app/config/`, `/app/fixtures/`, or `/tests/`.
