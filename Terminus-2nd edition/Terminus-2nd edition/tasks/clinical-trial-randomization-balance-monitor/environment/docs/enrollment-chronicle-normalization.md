# Enrollment chronicle normalization

accept-log sorts rows by ts ascending then seq ascending. Dedupe keeps the highest seq per subject_id and event pair. Withdrawn rows remain in history but are excluded later from active balance counts.
