## Export gate

`export::staging::publish_export` reads the snapshot, verifies `snapshot_digest` via `export::writer::verify_digest`, runs `export::validate::validate_snapshot`, and writes the merge r