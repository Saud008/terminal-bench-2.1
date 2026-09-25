# Snapshot version linkage

snapshot signed metadata carries targets_version.

During rotation verification, targets_version must equal targets signed version exactly.

Mismatch fails rotation even when individual signatures verify.
