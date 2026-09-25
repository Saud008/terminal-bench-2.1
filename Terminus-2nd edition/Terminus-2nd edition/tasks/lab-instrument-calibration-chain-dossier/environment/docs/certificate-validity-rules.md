# Certificate validity rules

## Validity window

A calibration certificate is valid on as_of_date when as_of_date is less than or equal to expires using ISO date lexicographic compare.

## Certificate digest

cert_digest is the first sixteen hex characters of SHA-256 over the UTF-8 string:

instrument_id:as_of_date:cert_id

Field order is mandatory. No extra separators or whitespace.
