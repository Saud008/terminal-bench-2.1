# Vault HMAC bind ticket

Vault HMAC bind tickets bind every `/gate/proof/check` call to the jkt pin
established at `/gate/session/open`.

## Formula

```
bind_ticket = hex(HMAC-SHA256(vault_key, principal || ":" || session || ":" || jkt))
```

- `vault_key` is the raw bytes decoded from `vault_hmac_key` (hex) in
  `/app/config/jktadmit.json`.
- `jkt` is the lowercase-hex thumbprint computed at open time from the open
  proof's embedded `jwk` (see `/app/docs/jkt-thumbprint-policy.md`).
- Output is lowercase hex encoding of the 32-byte MAC.

## Open

`POST /gate/session/open` verifies the presented proof, computes its `jkt`,
checks the pin registry, mints the ticket, and stores the session keyed by
`(principal, session)`. The JSON response includes both `bind_ticket` and
`jkt`.

## Pin registry and JKTADMIT_PIN_DIR

The pin registry is read from `<pin dir>/jkt_pins.json`. The pin directory
is resolved as follows, in order:

1. The `JKTADMIT_PIN_DIR` environment variable, if it is set and non-empty.
2. Otherwise, the `pin_dir` field from `/app/config/jktadmit.json`.

If `jkt_pins.json` does not exist at the resolved directory, the registry is
`{"mode": "allow_all"}` and every jkt is accepted at open. If it exists and
`"mode"` is `"allowlist"`, only a `jkt` present in the `"jkts"` array may
open; any other jkt is denied at open with reason `jkt_not_registered`.

## Check

`POST /gate/proof/check` must echo the exact bind ticket for that
principal+session. Mismatch or empty ticket increments
`deny_totals.ticket_invalid` and returns HTTP 409 with
`{"verdict": "deny", "reason": "ticket_invalid"}`.
