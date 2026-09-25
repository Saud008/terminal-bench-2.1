# Staging digest (canonical encoding)

Every ledger entry carries a digest over a canonical one-line encoding of the staged state.
Encoding is byte-exact: no padding, no spaces, decimal integers, lowercase hex digests.

## Field encodings

```
members = connected_ids joined with ","
          ascending by player_id; empty list encodes as the empty string

invites = for each staged pending invite "<invite_id>:<invitee_id>:<expires_mono_ms>",
          joined with ","
          ascending by expires_mono_ms, then invite_id; empty list encodes as the empty string
```

## State key (suppression only — never hashed)

```
state = status + "|" + leader_id + "|" + max_members + "|" + members + "|" + invites
```

The state key deliberately excludes `seq`, `party_seq`, `staged_mono_ms` and `sweep_epoch`:
a sweep that changes only the epoch is not a state change, and re-staging the same state twice
appends nothing (`/app/docs/audit-snapshot.md`).

## Entry line (hashed)

```
line = "pas/2|" + seq + "|" + party_id + "|" + party_seq + "|" + staged_mono_ms
       + "|" + sweep_epoch + "|" + state
```

## Digest

```
entry_digest = lowercase_hex( SHA-256( prev_digest + "|" + line ) )
GENESIS      = "0" * 64
```

`prev_digest` is the ledger `chain_head` at append time, so the digest binds every entry to the
whole history, including the sweep epoch each entry was staged under.

## Worked vector

Party `pty_demo`, leader `leader-a`, cap `4`. First entry — one pending invite staged at monotonic
`200` before any sweep, chaining from `GENESIS`:

```
state = active|leader-a|4|leader-a|inv_a1:guest-a:5200
line  = pas/2|1|pty_demo|1|200|0|active|leader-a|4|leader-a|inv_a1:guest-a:5200
entry_digest = b76a731bc3b2c737a7da6be696adf23c8d4329b7daec03eb3215d8803faff2f7
```

Second entry — `guest-a` accepted at monotonic `300`, so the invite leaves the pending list and the
member list grows; it chains from the digest above:

```
state = active|leader-a|4|guest-a,leader-a|
line  = pas/2|2|pty_demo|2|300|0|active|leader-a|4|guest-a,leader-a|
entry_digest = 4fb3ad366744c874627cecba44e889edfeab956e95450ac783a87904f479503f
```

## Non-authoritative helpers

`LegacySealDigest` in `/app/internal/audit/legacy_seal.go` and `LegacyCapGuard` in
`/app/internal/party/capwrap.go` are retained for an older checkpoint format. Neither is on the
staging or report-publication path; do not derive ledger digests or export occupancy from them.
