# Histogram unwrap labels

When a sample carries a le label, unwrap moves the target numeric field into the sample value and removes le plus the unwrapped field name from labels.

The _sum and _count sibling labels must remain on the sample after unwrap. They are required for downstream fingerprint grouping on histogram exports.
