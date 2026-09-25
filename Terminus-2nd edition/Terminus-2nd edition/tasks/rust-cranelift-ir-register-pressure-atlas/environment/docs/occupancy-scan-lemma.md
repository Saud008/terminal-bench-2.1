# Occupancy scan lemma

Walk the energy-ordered, non-vetoed fluence channels. Each channel occupies the closed
interval [energy_q, energy_q + width_q]. For every channel's own start point, count
how many surviving channels' intervals contain that point (inclusive both ends).
max_occupancy is the largest such count; the maximum overlap of a set of closed
intervals always occurs at one interval's start, so scanning starts alone is
sufficient.

peak_channel_id is the channel_id of the first channel (in energy order) whose start
point attains max_occupancy.

effective_aperture = max(1, aperture_budget + TB3_APERTURE_DELTA), where
TB3_APERTURE_DELTA is read fresh at emit-occupancy time only and defaults to 0 when unset. It
never mutates the ledger.

spill_risk = max_occupancy > effective_aperture.
