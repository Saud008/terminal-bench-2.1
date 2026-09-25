# Trace manifest schema

Required keys: run_id, trace_id, loss_threshold_db, reflection_tolerance_m, wavelength_nm, launch_power_dbm.
loss_threshold_db is the minimum adjacent-sample power drop that qualifies as a loss event.
reflection_tolerance_m groups events at nearby distances for duplicate suppression.
