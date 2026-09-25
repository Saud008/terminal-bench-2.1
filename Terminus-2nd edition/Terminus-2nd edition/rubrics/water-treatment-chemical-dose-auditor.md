# Platform rubric — water-treatment-chemical-dose-auditor

**Task folder:** tasks/water-treatment-chemical-dose-auditor/

Agent implements hydraulic contact gating before claiming flow-weighted dose is correct, +3
Agent normalizes percent lot concentrations with the 10000 multiplier from docs, +2
Agent converts m3/h flow readings to liters per minute using the 1000 over 60 rule, +2
Agent applies turbidity uplift with the 0.10 slope and 1.5 cap from the dose kernel doc, +3
Agent forward-fills sensor outage minutes only up to three consecutive gaps, +2
Agent validates operator overrides with case-insensitive role matching and denylist rejection, +2
Agent computes breach atlas rows only from the staged dose ledger without rereading shift bundles, +3
Agent sorts breach rows by descending severity then ascending chem_id, +2
Agent writes lot fingerprint digests using chem_id colon lot_code colon as_of field order, +2
Agent skips minutes below min_flow_lpm when accumulating contact_excluded_minutes, +2
Agent applies per-minute residual dose cap before summing total_dose_mg, +2
Agent publishes breach_atlas_seal as SHA-256 over sorted compact summary JSON, +3
Agent ignores decoy turbidity chart module on the export hot path, +1
Agent rebuilds wtcdctl with cargo release before running pytest, +2
Agent uses absolute /app paths cited in instruction without backticks, +1
Agent leaves guest.temp denylisted override factors out of dose totals, +2
Agent matches independent wtcda_refmath reference totals on bundled plant shifts, +3
Agent only edits environment modules and rebuilds instead of hardcoding pytest expectations, -3
Agent patches a single obvious unit conversion file and stops while ledger token stays wrong, -5
Agent reads shift bundle JSON directly inside emit-breach-atlas instead of the dose ledger, -5
Agent applies arithmetic mean concentration instead of flow-weighted mean, -3
Agent treats outage minutes as zero flow without forward-fill within three minutes, -3
Agent accepts supervisor override role with wrong ASCII case sensitivity, -2
Agent omits contact_excluded_minutes from ledger chemical rows, -2
