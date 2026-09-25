# Dangling manifest detection

An image manifest is dangling when no snapshot refs array in the scoped gc snapshot catalog contains its digest.

Namespace retention_pins list digests that must never appear in deletable_images even when no snapshot references them.
