# Scale revision epochs

Manifest scale_epochs[] holds revision records with epoch_id, effective_ms, factor, and offset.

## Selection

For each accepted frame, pick the latest epoch where effective_ms <= frame.received_ms. Never use device_clock_ms for epoch selection.

## Engineering value

engineering = raw * factor + offset using the selected epoch.

## Pin override

Per-register override scale_epoch forces that epoch_id when present, ignoring later epochs even if their effective_ms has passed.
