# placement-hash-contract.md

crush_hash concatenates pool_id, pg_num, bucket or host id, and retry counter with hashlib.sha256 in Python reference helpers. Weighted pick uses hash modulo normalized weight sum. ledger_digest sealing uses the same hashlib.sha256 json sort_keys pattern described in placement-trace-ledger-schema.md.
