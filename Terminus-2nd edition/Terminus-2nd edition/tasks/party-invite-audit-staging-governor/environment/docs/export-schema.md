# Export schema

`POST /v1/party/export` publishes the checkpoint-backed occupancy report to
`/app/output/party-audit.json`:

```json
{
  "party_id": "pty_demo",
  "leader_id": "leader-a",
  "status": "active",
  "max_members": 4,
  "connected_members": 2,
  "pending_invites": 1,
  "effective_occupancy": 3,
  "expired_pending_invites": 0,
  "orphan_party": false,
  "audit_seq": 7,
  "staged_party_seq": 3,
  "sweep_epoch": 1,
  "chain_head": "4fb3ad366744c874627cecba44e889edfeab956e95450ac783a87904f479503f",
  "reserved_slots": 1,
  "stale_staged_invites": 0
}
```

`export_mono_ms` below is the monotonic clock of the export request. **Staged entry** means the
newest retained ledger entry for the requested `party_id` (`/app/docs/audit-snapshot.md`).

## Refusal before publish

Export verifies the ledger before it writes anything. On refusal it answers **HTTP 400** with the
plain-text token below and **must not create or modify** `/app/output/party-audit.json`. Checks run
in this order and the first failure wins:

| Order | Condition | Token |
|-------|-----------|-------|
| 1 | ledger file missing, unreadable, or `snapshot_version` ≠ `2` | `audit ledger unavailable` |
| 2 | chain / digest / `seq` / `party_seq` verification fails | `audit ledger chain broken` |
| 3 | no retained entry for the requested party | `audit ledger party unstaged` |
| 4 | staged entry `status` is `retired` | `audit ledger party retired` |
| 5 | no live `parties` row for the party | `audit ledger party missing` |
| 6 | staged `status`, `leader_id` or `max_members` differ from the live `parties` row | `audit ledger drift` |

## Published fields

| Field | Derivation |
|-------|------------|
| `party_id`, `leader_id`, `status`, `max_members` | staged entry (not the live row) |
| `connected_members` | live `members` rows with `status = 'connected'` |
| `pending_invites` | live `invites` rows with `status = 'pending'` |
| `expired_pending_invites` | live pending rows with `expires_mono_ms <= export_mono_ms` |
| `reserved_slots` | see below — derived from the staged entry, reconciled against live members |
| `effective_occupancy` | `connected_members + reserved_slots` |
| `stale_staged_invites` | staged `pending_invites` with `expires_mono_ms <= export_mono_ms` |
| `orphan_party` | `true` when staged `status` is `active` and the live leader member row is not `connected` |
| `audit_seq`, `sweep_epoch`, `chain_head` | ledger header |
| `staged_party_seq` | `party_seq` of the staged entry |

## Reserved slots

`reserved_slots` counts seats still held by staged invitations, reconciled across both sources:

1. take the staged entry's `pending_invites`
2. drop every invite with `expires_mono_ms <= export_mono_ms`
3. drop every invite whose `invitee_id` is already a **connected member** of the party in live
   SQLite — an accepted invitee occupies a member seat, never a reserved seat as well
4. count the remaining **distinct** `invitee_id` values — two open invitations for the same
   invitee reserve one seat, not two

A published report therefore never counts a player twice, and `stale_staged_invites` stays `0` while
sweep refresh keeps the staged pending list current (`/app/docs/sweep-contract.md`).
