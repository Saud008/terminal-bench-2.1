# Epoch reset

Lowering sequence below the current high_water requires an epoch strictly greater than the stream epoch.

Resets without an epoch bump increment dedup_miss and leave the ledger unchanged.
