# Calibration register contract

calbind fuse upserts into /app/work/calibration-register.db table calibration_register.

Columns:

- batch_id TEXT PRIMARY KEY
- pack TEXT
- fuse_generation INTEGER
- payload_json TEXT (serialized staged instrument)

fuse_generation starts at 1 on first fuse for a batch id and increments by 1 on each subsequent fuse for that batch even when pack changes.

export reads only payload_json for the batch id.
