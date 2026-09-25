# Platform rubric — lab-instrument-calibration-chain-dossier

**Task folder:** tasks/lab-instrument-calibration-chain-dossier/

Agent composes certificate digest as instrument_id:as_of_date:cert_id per validity rules, +3
Agent resolves std_root from null-parent standard chain link, +3
Agent combines uncertainty budget components by root-sum-square not linear sum, +3
Agent requires instrument_id in technician scope_instruments for authorization, +3
Agent applies asymmetric tol_plus and tol_minus bands per channel reading, +3
Agent writes ingest vault staging snapshot keyed by batch id, +3
Agent increments fuse_generation monotonically on each fuse call, +3
Agent upserts register row without reloading pack JSON during export, +2
Agent exports expanded_uncertainty not combined_uncertainty in dossier rows, +3
Agent ranks dossier rows by severity descending before summary counters, +2
Agent binds dossier_digest including fuse_generation in export header, +2
Agent rebuilds calbind with cargo release before pytest in conftest, +2
Agent honors TB3_FIXTURE_DIR overlay for hidden calibration packs, +2
Agent leaves decoy spectrum_stub off ingest fuse export hot path, +2
Agent reverses certificate digest field order in line_validity module, -3
Agent sums uncertainty components linearly instead of RSS combine, -3
Agent authorizes technician without scope_instruments membership check, -3
Agent uses symmetric tolerance band around nominal for OOT decisions, -2
Agent reads pack fixtures during export after fuse completed, -3
Agent emits combined_uncertainty where expanded_uncertainty required, -2
