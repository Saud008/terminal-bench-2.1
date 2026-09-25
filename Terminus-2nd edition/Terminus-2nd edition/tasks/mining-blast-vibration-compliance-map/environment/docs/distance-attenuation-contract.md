# Distance attenuation contract

Numerical reference math for predicted PPV at each property compliance anchor.

For each blast and property compliance anchor, compute distance_m as the Euclidean distance in mine-site meters between the blast epicenter easting/northing and the compliance anchor from the boundary contract.

Predicted PPV at the anchor before calibration blending:

  attenuated_ppv = source_ppv_mm_s * (reference_distance_m / distance_m) ** attenuation_exponent

Use the survey reference_distance_m and attenuation_exponent. distance_m must be strictly positive; use the computed anchor distance, not sensor coordinates.
