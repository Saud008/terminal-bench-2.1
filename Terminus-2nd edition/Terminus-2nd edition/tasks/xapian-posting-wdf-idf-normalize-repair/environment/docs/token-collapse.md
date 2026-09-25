# Positional collapse

Tokenize document body by splitting on ASCII whitespace and lowercasing. Positional collapse merges each maximal run of adjacent identical tokens into a single collapsed slot before any within-document frequency or length computations.

Example: body "rust rust memory rust" yields collapsed slots [rust, memory, rust]. Term rust has slots(t, d) = 2 and memory has slots(t, d) = 1. WDF must be computed only after this collapse step completes.
