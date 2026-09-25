# Coincidence veto gate

A channel is veto-killed when its quantized energy_q falls inside any veto window
[quantize(lo_kev), quantize(hi_kev)], inclusive on both ends. Quantize both window
bounds with the same micron-eV scale used for the channel energies before comparing.

Veto-killed channels carry vetoed = true and residual_counts = 0 in the ledger. They
are excluded from channel_order, the occupancy scan, and closure rows.
