# Replica membership

Config `add_voter` applies at its log index if `term >= membership_epoch_term`. `remove_voter` drops the node immediately. Membership lists stay sorted ascending.

Queue payload `replicas` is advisory; export replica set equals membership after replay (sorted).

## audit-membership report

`/app/work/replica-membership-report.json` fields:

- `cluster`, `scenario`
- `member_count` — `len(membership)`
- `voter_ids` — staging membership list
- `finding_count` — **equal to `member_count` / `len(membership)`** (voter inventory size). It is not an error/violation counter; a healthy three-voter cluster reports `finding_count >= 1` (typically 3).
