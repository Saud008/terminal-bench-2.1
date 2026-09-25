# Object Lock billing freeze

If **any** version of an object key has legal_hold true, or retention_until strictly after window_end, **all** versions of that key freeze tier moves and expiration for charge simulation.

holds.json may list additional key prefixes under legal_hold_prefixes; any key starting with a listed prefix is treated as frozen for billing.

Frozen keys still appear in suppressed_keys and contribute bytes at their current storage_class for the monthly rollup.
