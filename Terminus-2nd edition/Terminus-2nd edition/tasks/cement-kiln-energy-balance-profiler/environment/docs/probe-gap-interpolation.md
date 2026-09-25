# Probe gap interpolation

After calibration (temp_c = temp_norm_c - cal_offset_c), build a uniform grid from min to max observed probe_ts stepping grid_step_sec from config.

When a grid probe_ts lacks an exact sample, linearly interpolate between the nearest lower and upper calibrated samples. Mark interpolated true. Exact hits mark interpolated false.
