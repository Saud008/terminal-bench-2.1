# Pairing gate contract

A device is blocked with reason `ineligible_pairing_required` when all three of the following hold:

1. `trusted` is `true`.
2. `addr_type` does not equal `bonded_addr_type`.
3. `pairing_confirmed` is `false`.

If `addr_type` equals `bonded_addr_type`, the device's link-layer address has not drifted since the original bond, and this gate never blocks the device regardless of `pairing_confirmed`.

If `trusted` is `false`, this gate never blocks the device, because an untrusted device is not eligible for silent reconnect in the first place and is out of scope for this gate (other gates may still apply).
