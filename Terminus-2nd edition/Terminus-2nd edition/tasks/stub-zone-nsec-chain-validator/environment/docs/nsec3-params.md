# NSEC3 parameters

Zone-level nsec3_params in the capture define salt_hex, iterations, and hash_algorithm for stub proofs.

Each NSEC3 record may carry per-record salt_hex and iterations. Before accepting an NSEC3 record as covering a query, the validator must confirm that record iterations equals zone iterations when the record iterations field is non-zero. Mismatched iteration counts invalidate the proof even when the hash owner window would otherwise cover the qname.

Hash owner and next_hashed comparisons use lowercase hex. Covering uses the zone iteration count for hash computation, not a stale per-record iteration unless the record explicitly matches zone params.
