# Platform rubric — seedlink-polarity-phase-window-catalog

**Task folder:** tasks/seedlink-polarity-phase-window-catalog/
**Category:** Scientific Computing (zip `scientific-computing`; phase-window metrology laboratory closure)

Agent validates SLWS CRC before pick chronology parse on decode path, +3
Agent rejects duplicate pick sample_idx on decode-only invariant path, +3
Agent writes phase-staging snapshot under /app/state/phase-staging before catalog export, +3
Agent computes staging digest over sample_idx sorted pick rows, +3
Agent applies leap-second table membership adjustment to pick center_us, +3
Agent resolves effective_polarity from station sheet over body hint, +3
Agent computes clipped_fraction with LSB-first clip mask inside window, +2
Agent exports catalog JSON from on-disk staging without reparsing SLWS picks, +3
Agent honors TB3_LEAP_ROOT for hidden leap chronology calibration table, +2
Agent honors TB3_POLARITY_ROOT for hidden polarity calibration sheets, +2
Agent preserves source and stem fields in staging snapshot public API, +2
Agent applies phase window pre and post microsecond bounds per contract, +2
Agent rebuilds seedcat with cargo release before pytest in test.sh, +2
Agent leaves decoy legacy_wrap module off export hot path, +2
Agent reads tampered on-disk staging picks on second export invocation, +2
Agent sorts export windows with calibrated center_us from leap closure, +1
Agent reparses SLWS for pick rows when staging snapshot already exists, -3
Agent computes staging digest from unsorted file-order pick rows, -3
Agent skips leap adjustment when leap_marker set on listed epoch, -3
Agent uses body_polarity hint when station sheet defines override, -3
Agent applies MSB-first clip mask bit order for clipped_fraction, -2
Agent writes catalog export without intermediate staging artifact, -2
Agent ignores TB3 hidden leap table when TB3_LEAP_ROOT set, -2
Agent mutates staging_version away from STAGING_VERSION contract, -2
