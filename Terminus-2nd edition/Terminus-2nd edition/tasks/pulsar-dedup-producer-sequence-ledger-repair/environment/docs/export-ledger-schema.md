# Export ledger schema

Export JSON contains tenant, streams map keyed by producer|topic, and export_barrier_ok boolean.

Each stream entry includes epoch, high_water, broker_acked_max, dedup_miss, duplicate_replay, and accepted_count integers.
