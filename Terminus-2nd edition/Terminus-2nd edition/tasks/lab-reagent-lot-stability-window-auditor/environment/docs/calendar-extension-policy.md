# Calendar extension policy

extended_expiry parses base_expiry as an ISO calendar date, then advances by cold_chain_days plus stability_bonus_days as whole calendar days. Do not take the maximum of the two day counts; always sum them.
