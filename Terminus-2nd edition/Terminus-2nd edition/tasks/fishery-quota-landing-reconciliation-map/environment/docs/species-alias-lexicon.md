# Species alias lexicon

Landing species_code values may arrive as regional codes. Resolve each code to a lexicon species key before conversion or quota lookup.

Rules:
- Trim whitespace and compare case-insensitively.
- If the code equals a lexicon key, use that key.
- If the code equals any alias listed under a lexicon key, use that lexicon key.
- Otherwise use the uppercased trimmed raw code.

Example: aliases map COD to GAD and GADUS. A landing with species_code GAD resolves to COD.
