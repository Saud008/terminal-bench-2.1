# Residual lemma

For each channel, residual_counts = measured_counts - background_at(energy_kev).

background_at(E) piecewise-linear interpolates between background_anchors sorted by
energy_kev. Below the lowest anchor energy, background_at returns the lowest anchor's
counts (flat extrapolation). Above the highest anchor energy, it returns the highest
anchor's counts. Between two consecutive anchors a and b, background_at(E) = a.counts
+ (b.counts - a.counts) * (E - a.energy_kev) / (b.energy_kev - a.energy_kev).

Veto-killed channels never run this lemma; their residual_counts is fixed at 0.
