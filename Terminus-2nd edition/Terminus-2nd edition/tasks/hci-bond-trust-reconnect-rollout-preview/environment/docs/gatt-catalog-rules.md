# GATT catalog contract

Each device lists `gatt_uuids`, the GATT service UUIDs discovered during the original bond. Entries may repeat with different case (for example `180F` and `180f` refer to the same service).

`gatt_service_count` for a device is the count of distinct UUIDs after lowercasing every entry, not the raw length of `gatt_uuids`. For example `["180F", "180f", "180A"]` has `gatt_service_count` equal to `2`.

`gatt_service_count` is never a blocking condition on its own; it is carried into the reconnect ledger and rollout atlas as a descriptive field on every eligible device row.
