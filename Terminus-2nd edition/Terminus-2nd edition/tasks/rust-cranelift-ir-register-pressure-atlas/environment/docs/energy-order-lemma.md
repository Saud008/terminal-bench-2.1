# Energy order lemma

Fluence channels and every derived scan use one canonical order: quantized energy_q
ascending, tie-broken by channel_id ascending (lexicographic). This order applies to
the persisted ledger channel list, the occupancy scan walk, and the channel_order
field of the closure atlas.
