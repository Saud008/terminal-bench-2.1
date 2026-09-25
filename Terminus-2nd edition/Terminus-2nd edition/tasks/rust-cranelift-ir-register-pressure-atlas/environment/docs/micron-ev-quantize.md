# Micron-eV quantization

For scale S = micron_ev_scale (default 1000, overridable by TB3_MICRON_EV_SCALE at
accrue time), each raw value v (an energy_kev or width_kev) quantizes to
round_half_away_from_zero(v * S) / S, where round_half_away_from_zero rounds ties
away from zero rather than toward even or toward zero.

Both energy_kev and width_kev on every channel are quantized this way before any
downstream lemma runs. Veto window lo_kev/hi_kev are quantized identically before the
coincidence check.
