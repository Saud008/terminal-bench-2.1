# FITS card lexicon

Split each card on the first `=`. Trim whitespace around the keyword and value.
Keywords are the trimmed left-hand side (for example `CRVAL1`, `CTYPE1`).
When a value is wrapped in single quotes, strip the surrounding quotes so
`CTYPE1  = 'RA---TAN'` yields value `RA---TAN`.
