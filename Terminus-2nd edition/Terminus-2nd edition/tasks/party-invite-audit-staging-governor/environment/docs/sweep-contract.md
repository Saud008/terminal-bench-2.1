# Sweep contract

`POST /v1/admin/sweep` uses the **monotonic test clock** (`X-Test-Mono-Ms` when set, otherwise
process monotonic ms) and answers:

```json
{ "expired_invites": 1, "removed_parties": 0, "retired_parties": 0, "sweep_epoch": 1 }
```

`sweep_epoch` is the ledger epoch **after** this sweep; `retired_parties` counts retirement entries
this sweep appended.

## 1. Expire invites

Mark invites `expired` where:

```
status = 'pending' AND expires_mono_ms <= now_mono_ms
```

Never use wall-clock `time.Now()` for TTL comparison.

## 2. Remove disbanded parties

Delete `parties` rows with `status = 'disbanded'` and no connected members.

## 3. Bump the epoch

Increment the ledger `sweep_epoch` by `1` and persist it, **before** any re-staging in step 4, so
every entry this sweep appends carries the new epoch in its hashed line
(`/app/docs/staging-digest.md`). The bump persists even when the sweep appends no entry at all.

## 4. Refresh staged parties

Re-stage **every** row in `parties` — active and disbanded alike — ascending by `party_id`.
Suppression from `/app/docs/audit-snapshot.md` applies, so a party whose state key did not change
appends nothing: a sweep that expires nothing leaves `entries` untouched while the epoch still
advances.

Because expiry removes rows from the staged pending list, `stale_staged_invites` in the next
published report is `0` (`/app/docs/export-schema.md`); a sweep that updates SQLite without
refreshing the ledger leaves the report reserving seats for dead invitations.

## 5. Retire vanished parties

After step 4, for every `party_id` in the ledger `party_seqs` map that has **no** `parties` row,
append a retirement entry — ascending by `party_id`, after all refresh entries of this sweep:

| Retirement entry field | Value |
|------------------------|-------|
| `status` | `retired` |
| `leader_id`, `max_members` | carried from that party's newest retained entry |
| `connected_ids`, `pending_invites` | `[]` |
| `staged_mono_ms`, `sweep_epoch` | this sweep's monotonic clock and new epoch |
| `seq`, `party_seq`, `prev_digest`, `entry_digest` | normal append rules |

Skip a `party_id` when it has no retained entry left to carry identity from, or when its newest
retained entry is already `retired` — suppression keeps a party retired exactly once. Retired
parties are refused at export with `audit ledger party retired`.
