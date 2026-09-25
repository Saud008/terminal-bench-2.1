# Loss event detection

Numerical calibration compares each sample to the previous sample at strictly lower distance_m in lab OTDR units.
When previous_power_dbm minus current power_dbm is at least loss_threshold_db, emit a loss event at current distance_m.
Record measured_loss_db as the delta rounded to three decimals.
