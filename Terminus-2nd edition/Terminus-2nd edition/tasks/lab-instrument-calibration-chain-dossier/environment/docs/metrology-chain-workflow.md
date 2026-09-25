# Metrology chain workflow

Phase one ingest loads a calibration pack and writes the intake vault snapshot.

Phase two fuse reads the vault entry and upserts the SQLite register row with incremented fuse_generation.

Phase three export reads only the register row and writes dossier JSON.

Export must not read pack fixtures or the intake vault.
