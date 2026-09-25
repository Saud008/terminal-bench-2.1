# Pairing / Address-Type Gate

Each bonded device record carries the `addr_type` (`public` or `random`) it
was seeded with, plus a `trusted` flag and a `pairing_confirmed` flag.

A `connect` operation supplies its own `addr_type`. The gate evaluates as
follows, in order:

1. If the device is not `trusted`, the connect is always allowed.
2. If the connect's `addr_type` matches the device's bonded `addr_type`,
   the connect is allowed.
3. Otherwise (trusted device, mismatched address type) the connect is only
   allowed if the device has an outstanding `pairing_confirmed` flag from a
   prior `pairing_confirm` operation. If not, the connect is rejected with
   `reason: pairing_required` and no `connect` ledger row is written for it
   — only a `connect_rejected` row.

A successful `disconnect` clears the device's `pairing_confirmed` flag, so a
later address-type-mismatched reconnect must be re-confirmed.

`pairing_confirms` in the midstate snapshot counts every `pairing_confirm`
operation processed, regardless of whether a later connect uses it.
