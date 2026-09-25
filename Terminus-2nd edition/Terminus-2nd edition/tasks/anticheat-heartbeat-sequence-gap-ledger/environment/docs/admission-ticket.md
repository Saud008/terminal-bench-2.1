# Admission ticket

Vault HMAC admission tickets bind every attest batch to a trust bind event.

## Formula

```
admission_ticket = hex(HMAC-SHA256(vault_key, token || ":" || session_id || ":" || decimal_anchor_mono_ms))
```

- `vault_key` is the raw bytes decoded from `vault_hmac_key` (hex) in `/app/config/livattest.json`
- `decimal_anchor_mono_ms` is the monotonic millisecond value recorded at bind (same value returned in the bind path via the clock pin)
- Output is lowercase hex encoding of the 32-byte MAC

## Bind

`POST /v1/trust/bind` mints the ticket and stores it on the session row. The JSON response includes `admission_ticket`.

## Batch

`POST /v1/attest/batch` must echo the exact ticket for that token+session. Mismatch or empty ticket increments `ticket_rejections` and returns HTTP 400.
