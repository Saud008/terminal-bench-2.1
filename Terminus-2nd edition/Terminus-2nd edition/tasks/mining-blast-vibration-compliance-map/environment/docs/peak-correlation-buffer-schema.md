# Peak correlation buffer schema

Path: /app/state/peak-correlation-buffer.json

Fields:
- correlate_seq: monotonically increasing unsigned integer starting at 1 on first load-survey for a seed
- seed: opaque seed string from CLI
- survey: survey name matching fixtures
- record: full survey payload including blasts, properties, sensors, readings, limits, reference_distance_m, attenuation_exponent, timezone_offset_hours

Each load-survey for the same seed increments correlate_seq even when the survey name changes.
