# Platform rubric — cement-kiln-energy-balance-profiler

**Task folder:** tasks/cement-kiln-energy-balance-profiler/

Agent converts Kelvin telemetry to Celsius before calibration per therm-unit-contract, +3
Agent converts kcal fuel CV to MJ energy_in before residual scoring, +3
Agent applies calibration offsets with correct sign on normalized Celsius probes, +3
Agent maps fuel batches onto probe windows using inclusive start_ts end_ts lineage, +3
Agent linearly interpolates missing probe grid samples instead of forward-fill, +3
Agent scores heat balance residual as energy_in minus clinker energy minus heat_loss, +2
Agent writes probe-grid JSON after interpolate-probes before score-balance, +2
Agent emits lineage_digest and audit_digest on published heat balance ledger, +2
Agent blocks publish-ledger when interpolate-probes or score-balance stages were skipped, +2
Agent honors TB3_CAL_TABLE override for hidden calibration table bundles, +2
Agent sorts probe_windows by ascending probe_ts in final ledger output, +2
Agent leaves grade_decoy module off the kilnbal CLI hot path, +2
Agent patches therm conversion only while fuel lineage windows stay exclusive, -3
Agent subtracts calibration offset instead of adding per probe-cal contract, -3
Agent forward-fills gap samples breaking linear interpolation grid tests, -3
Agent publishes ledger after load-probes and bind-fuel without interpolate stage, -3
Agent uses strict exclusive batch windows dropping boundary probe samples, -3
Agent omits heat_loss_mj from residual numerator inflating balance score, -2
