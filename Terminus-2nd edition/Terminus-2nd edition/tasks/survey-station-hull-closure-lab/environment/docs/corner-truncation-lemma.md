# Microdegree quantization

For scale S = microdegree_scale (default 10000, overridable by TB3_MICRO_SCALE), each residual
coordinate v becomes trunc(v * S) / S where trunc is toward-zero truncation.

residual_area_u64 is computed from the quantized axis-aligned bbox as
round((max_x - min_x) * S) * round((max_y - min_y) * S) when both widths are strictly positive,
otherwise zero.
