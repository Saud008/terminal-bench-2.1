# Spectrometer readings TSV

Path: readings.tsv inside each scenario bundle.

Header row required: batch_id, reading_id, L, a, b, measured_at_epoch, spectrometer_id

Duplicate reading_id values keep the last row in file order. All LAB fields are decimal numbers. measured_at_epoch is Unix seconds UTC.
