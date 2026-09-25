# Ring-fluence ledger schema

Path: /app/scratch/ring-fluence/<campaign-id>.json

Fields:
- accrual_epoch: monotonically increasing unsigned integer; first accrue for a campaign writes 1
- campaign_id: opaque campaign identifier from CLI
- bundle: bundle name matching fixtures
- micron_ev_scale: integer scale used for quantization
- aperture_budget: aperture headroom carried from the bundle
- dwell_width_kev: bundle dwell width metadata carried through unchanged
- channels: fluence channel records with channel_id, energy_q, residual_counts, width_q, vetoed

Channels are sorted by energy_q ascending, then channel_id ascending. Each accrue for the
same campaign id increments accrual_epoch even when the bundle name changes.
