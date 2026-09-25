# Volume completeness score

expected_gate_count equals manifest expected_ray_count times manifest expected_gate_bins times tilt_count after elevation sort. coverage_fraction equals valid_gate_total divided by expected_gate_count rounded to four decimal places. Using tilt_count alone as the denominator is invalid.

Sparse bundles with fewer rays than manifest expected_ray_count yield coverage_fraction below one when valid gates are counted correctly.
