# Party HTTP contract

Base URL: `http://127.0.0.1:8080`

All admin endpoints accept optional header `X-Test-Mono-Ms` (int64) to pin the service monotonic clock.

## POST /v1/party/create

Body:

```json
{ "leader_id": "string", "max_members": 4 }
```

- `leader_id` required.
- `max_members` optional; clamp to `[2, 8]`. Default from `/app/config/party.json` (`max_members`).

Response `200`:

```json
{ "party_id": "string", "leader_id": "string", "max_members": 4 }
```

## POST /v1/party/{partyId}/invite

Body:

```json
{ "invitee_id": "string", "ttl_ms": 30000 }
```

- `invitee_id` required.
- `ttl_ms` optional; default `default_invite_ttl_ms` from config.
- Reject with **409** when the party is disbanded, leader disconnected, or effective occupancy would meet/exceed cap.

Response `200`:

```json
{ "invite_id": "string", "expires_mono_ms": 30000 }
```

`expires_mono_ms = now_mono_ms + ttl_ms`.

## POST /v1/invite/{inviteId}/accept

Header `Idempotency-Key` required (opaque string).

Body:

```json
{ "invitee_id": "string" }
```

- Must match invite row.
- **409** when party disbanded, leader disconnected, invite expired, invite not pending, or cap exceeded.
- On success the invite becomes `accepted` and a connected member row is inserted atomically.
- Retries with the same idempotency key return the original HTTP status and JSON body without duplicating membership.

Response `200`:

```json
{ "party_id": "string", "invitee_id": "string", "status": "joined" }
```

## POST /v1/party/{partyId}/disconnect

Body:

```json
{ "player_id": "string" }
```

When the **leader** disconnects, the party is **disbanded**: status `disbanded`, all members disconnected, pending invites revoked. No orphan active party rows may remain.

Response `200`:

```json
{ "party_id": "string", "status": "disbanded" }
```

For non-leader disconnect, only that member is marked disconnected.

## POST /v1/admin/sweep

Runs TTL expiry, orphan cleanup, and audit staging refresh (`/app/docs/sweep-contract.md`).
Response `200`:

```json
{ "expired_invites": 0, "removed_parties": 0, "retired_parties": 0, "sweep_epoch": 1 }
```

## POST /v1/party/export

Body:

```json
{ "party_id": "string" }
```

Writes `/app/output/party-audit.json` using the export schema in `/app/docs/export-schema.md`.

Export is a verifier as well as a writer: when the audit staging ledger fails a check it answers
**400** with the matching plain-text token from `/app/docs/export-schema.md` and leaves
`/app/output/party-audit.json` untouched.
