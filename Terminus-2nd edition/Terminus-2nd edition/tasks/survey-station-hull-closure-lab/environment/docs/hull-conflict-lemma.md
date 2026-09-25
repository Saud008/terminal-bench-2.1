# Residual conflict gate

Two lattice stations conflict when both residual_area_u64 values are strictly positive and
their quantized bboxes have open-interval overlap on both axes:

  a.min_x < b.max_x && b.min_x < a.max_x && a.min_y < b.max_y && b.min_y < a.max_y

Degenerate zero-area hulls never conflict. A conflict rejects the entire bind and clears
the campaign lattice file.
