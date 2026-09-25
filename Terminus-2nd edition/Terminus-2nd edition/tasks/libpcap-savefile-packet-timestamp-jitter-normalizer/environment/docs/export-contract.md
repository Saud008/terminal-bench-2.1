Export reads staging and writes timeline JSON to --output with:

packets: array of {index, norm_ns, incl_len, orig_len} in tolerance-ordered sequence (index preserves original capture index).

stats: {gap_count, trunc_penalty_total_ns, packet_count}.

Export must append gap ledger rows per gap-ledger.md and update gap-seq.txt. Export must not rewrite staging.

Malformed staging or missing files exit code 2. Missing inputs exit code 1. Success exit code 0.
