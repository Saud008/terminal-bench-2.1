# GATT UUID Identity

`gatt_discover` operations report a `mac` and a `uuid`. UUIDs are
case-insensitive: `0000180F-0000-1000-8000-00805F9B34FB` and
`0000180f-0000-1000-8000-00805f9b34fb` identify the same characteristic.

The identity for deduplication purposes is the pair `(mac, uuid.lower())`.
`gatt_resolve_count` in the midstate snapshot counts each distinct
`(mac, uuid.lower())` pair **once**, no matter how many times it is
rediscovered across the trace (including case variants). Every
`gatt_discover` operation, whether or not it increments the counter, still
records a ledger row with the lower-cased `uuid`.
