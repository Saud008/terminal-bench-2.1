# Coordinate grid

Each chunk record includes coord_labels: one float per dimension. Compute:

    label[i] = origin[i] * scale

where scale is the effective_attrs key scale as f64 when present, otherwise 1.0.

coord_consistent is true when:

- index origin equals the row-major linear decode origin for the chunk index, and
- every coord_labels entry is finite.

Export sets dataset coordinate_ok false if any chunk for that dataset has coord_consistent false.
