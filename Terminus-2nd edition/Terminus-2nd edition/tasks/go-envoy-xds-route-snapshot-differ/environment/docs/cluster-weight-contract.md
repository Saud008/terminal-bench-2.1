# Cluster endpoint weight normalization

Per cluster, endpoint weights normalize to integers summing to 100.

Use largest-remainder rounding when proportional scaling yields a non-100 sum.

TB3_WEIGHT_SCALE may override the target sum on verifier-only runs.
