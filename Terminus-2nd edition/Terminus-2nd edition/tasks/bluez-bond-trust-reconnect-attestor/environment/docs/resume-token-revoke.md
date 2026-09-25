# Resume Token Revocation

`seed_bond` may set a non-empty `resume_token` for a device.

A `bond_remove` operation for that `mac`:

- Clears `bonded`, `trusted`, and `pairing_confirmed` to `false`.
- Clears `resume_token` to the empty string.
- If the device had a non-empty `resume_token` at the moment of removal,
  increments `resume_tokens_cleared` in the midstate snapshot by one. Removing
  a device with no outstanding token does not increment the counter.

Because `bond_remove` also clears `trusted`, any `connect` that follows a
bond removal for the same `mac` is evaluated against an untrusted device
record and is therefore always allowed by the pairing/address-type gate,
independent of the address type it presents.
