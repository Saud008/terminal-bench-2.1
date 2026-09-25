# Hold rollup contract

compose-rollup writes /app/state/hold-queue-rollup.json with keys:

- scenario
- engine (holdfairctl)
- rollup_fingerprint (sha256 hex over transformed hold ledger rows)
- hold_request_count
- patron_count

rollup_fingerprint covers unique patron_id values sorted ascending, then each hold request_id:item_id in database order, then catalog_seed.
