# Dynamic dimension symbols

symbol_links declare equality between symbolic names. Each entry is an ordered pair [left, right]. Equality is transitive: when links connect N to batch and batch to K, all three names refer to one symbolic dimension during concat and matmul checks.

## Canonical representative (left-biased)

Process symbol_links in array order. For each pair [left, right], merge the two names with left-biased union-find:

1. Resolve left and right to their current canonical representatives (roots).
2. If the roots differ, attach the right root under the left root. The left root becomes the canonical name for the merged set.
3. Path compression is allowed, but the canonical string must remain the left-biased root after all links are applied.

Example: links [[N, batch], [K, N]] yield canonical K for N, batch, and K. The first merge attaches batch under N; the second pair has left root K and right root N, so N is attached under K and K becomes the set representative.

After links are applied, materialize replaces every symbolic string with its canonical representative before operator rules run.
