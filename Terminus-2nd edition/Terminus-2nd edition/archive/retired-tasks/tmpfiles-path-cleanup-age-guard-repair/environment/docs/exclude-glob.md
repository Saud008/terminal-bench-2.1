# Exclude glob depth

Each r! line may include an optional eN suffix where N is a non-negative integer exclude depth.

For a remove rule with anchor directory D (dirname of the first literal segment in the GLOB) and candidate path C matched by the GLOB:

Compute depth as the number of path components in C relative to D (minimum 1 for files directly under D).

An x GLOB exclude suppresses removal of C only when:

1. C matches the x GLOB, and
2. depth is less than or equal to N.

When N is omitted, treat N as 0 (only exact-depth-one children may be excluded). Excludes never apply across unrelated remove rules.

Nested ** globs follow shell globstar semantics against the synthetic tree paths map.
