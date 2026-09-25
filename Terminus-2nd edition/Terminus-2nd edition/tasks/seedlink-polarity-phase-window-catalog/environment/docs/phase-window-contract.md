# Phase window and polarity calibration contract

Numerical closure rules for seismic phase-window catalog export. See `/app/docs/scientific-computing-workflow.md` for calibration scope and reference math tolerance.

## Polarity sheets

Station polarity corrections live at /app/config/polarity/<network>.pol as JSON maps from station id string to signed integer polarity (-1, 0, +1). effective_polarity for a snippet is the sheet value when present, otherwise body_polarity from the SLWS header.

When TB3_POLARITY_ROOT is set to an absolute directory, load <network>.pol from that directory instead of /app/config/polarity.

## Phase windows (microseconds)

| Phase | Pre-window | Post-window |
|-------|------------|-------------|
| P | 2_000_000 | 4_000_000 |
| S | 3_000_000 | 5_000_000 |
| X | 1_000_000 | 1_000_000 |

center_us = epoch_sec * 1_000_000 + sample_idx * period_us + leap_adjust_us

period_us = (1_000_000 * 1000) / rate_mhz

start_us = center_us - pre_window
end_us = center_us + post_window

## Clipped fraction

Within the inclusive sample index window derived from start_us and end_us, clipped_fraction is the fraction of samples whose clip_mask bit is set. Bits are LSB-first within each mask byte.

## Polarity label

peak_amplitude is the signed value of the maximum-by-absolute-value sample inside the window (equivalent to `max(window, key=abs)` - not `abs` of that peak, and not the sample at `pick_sample`). polarity label is up when effective_polarity multiplied by that signed peak_amplitude is positive, down when negative, unknown when zero.

## Temporal invariant flag

invariant_ok in export windows is true when every pick sample_idx is unique and less than sample_count.
