# Audit staging ledger

Party occupancy reporting is a **two-stage** pipeline over one durable checkpoint ledger:

1. **Stage** — every lifecycle mutation (invite, accept, disconnect) and every admin sweep appends
   to `/app/state/party-audit-snapshot.json`.
2. **Publish** — export verifies the ledger chain, then seals occupancy from the newest retained
   entry of the requested party into `/app/output/party-audit.json`.

Publish must **not** re-derive reserved occupancy from SQLite invite rows. Live SQLite still owns
the raw pending / expired counters (`/app/docs/export-schema.md`).

Canonical field encodings and the digest are defined in `/app/docs/staging-digest.md`.

## Ledger file

`/app/state/party-audit-snapshot.json`

```json
{
  "snapshot_version": 2,
  "audit_seq": 2,
  "sweep_epoch": 0,
  "chain_base": "0000000000000000000000000000000000000000000000000000000000000000",
  "chain_head": "4fb3ad366744c874627cecba44e889edfeab956e95450ac783a87904f479503f",
  "party_seqs": { "pty_demo": 2 },
  "entries": [ … ]
}
```

| Header field | Meaning |
|--------------|---------|
| `snapshot_version` | Ledger schema version — always `2` |
| `audit_seq` | `seq` of the newest entry ever appended; `0` before the first append |
| `sweep_epoch` | Completed admin sweeps; `0` before the first sweep (`/app/docs/sweep-contract.md`) |
| `chain_base` | Digest the retained window chains from — `GENESIS` until an entry is evicted |
| `chain_head` | `entry_digest` of the newest retained entry — `GENESIS` while `entries` is empty |
| `party_seqs` | Durable per-party counter: highest `party_seq` ever appended for that `party_id` |
| `entries` | Retained window, **oldest first**, at most `8` entries |

`GENESIS` is 64 `0` characters.

## Entry

```json
{
  "seq": 1,
  "party_seq": 1,
  "party_id": "pty_demo",
  "leader_id": "leader-a",
  "status": "active",
  "max_members": 4,
  "staged_mono_ms": 200,
  "sweep_epoch": 0,
  "connected_ids": ["leader-a"],
  "pending_invites": [
    { "invite_id": "inv_a1", "invitee_id": "guest-a", "expires_mono_ms": 5200 }
  ],
  "prev_digest": "0000000000000000000000000000000000000000000000000000000000000000",
  "entry_digest": "b76a731bc3b2c737a7da6be696adf23c8d4329b7daec03eb3215d8803faff2f7"
}
```

The staged party state is read from live SQLite at stage time:

| Entry field | Source |
|-------------|--------|
| `leader_id`, `status`, `max_members` | the `parties` row (`status` is `active` or `disbanded`) |
| `connected_ids` | `members.player_id` where `status = 'connected'`, **ascending by `player_id`** |
| `pending_invites` | `invites` rows where `status = 'pending'`, **ascending by `expires_mono_ms`, then `invite_id`** |
| `staged_mono_ms` | monotonic clock of the mutation that staged the entry |
| `sweep_epoch` | ledger `sweep_epoch` at stage time |

`revoked`, `expired` and `accepted` invite rows are never staged. Empty lists are `[]`, never `null`.

Retirement entries (`status = "retired"`) are appended by sweep only — see
`/app/docs/sweep-contract.md`.

## Append rules

A stage attempt computes the party state, then:

1. **Suppression** — when the party already has an entry inside the retained window and that
   entry's **state key** equals the recomputed state key, the ledger file is left unchanged:
   no entry, `audit_seq`, `chain_head`, `chain_base` and `party_seqs` all unchanged.
   The comparison is against **that party's** newest retained entry — never against the newest
   entry of the ledger, and never against an entry of another party. A party with no retained
   entry always appends.
2. **Append** — otherwise:
   - `seq` = header `audit_seq` + 1 (global, contiguous, never reused)
   - `party_seq` = `party_seqs[party_id]` + 1 (durable per party; retention never rewinds it)
   - `prev_digest` = header `chain_head` before the append
   - `entry_digest` = digest of `prev_digest` and the entry line (`/app/docs/staging-digest.md`)
   - header `audit_seq`, `chain_head`, `party_seqs[party_id]` are updated from the new entry
3. **Retention** — the ledger keeps the newest `8` entries. When an append evicts entries,
   `chain_base` becomes the `entry_digest` of the **newest evicted** entry, so
   `entries[0].prev_digest` always equals `chain_base`.

The ledger is the only durable staging state: `audit_seq`, `sweep_epoch`, `party_seqs`,
`chain_base` and `chain_head` survive daemon restarts because they are read back from the file.

## Chain verification

Export refuses to publish unless all of the following hold (`/app/docs/export-schema.md`):

- `snapshot_version` is `2`
- `entries[0].prev_digest` equals `chain_base`, and each later entry's `prev_digest` equals the
  previous entry's `entry_digest`
- every `entry_digest` recomputes from `prev_digest` and the entry line
- `seq` values are contiguous and ascending, and the last one equals `audit_seq`
- `chain_head` equals the last `entry_digest` (or `GENESIS` when `entries` is empty)
- inside the retained window each party's `party_seq` values strictly increase, and none exceeds
  `party_seqs[party_id]`
