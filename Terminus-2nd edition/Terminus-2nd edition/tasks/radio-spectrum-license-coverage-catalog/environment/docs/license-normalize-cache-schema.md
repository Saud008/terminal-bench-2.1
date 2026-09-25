# License normalize cache schema

Path: /app/state/rf-grant-wal.json

Fields:
- load_generation: monotonically increasing unsigned integer starting at 1 on first index-grants for a seed
- seed: opaque seed string from CLI
- bundle: bundle name matching fixtures
- as_of_date: ISO date copied from bundle
- licenses: flattened license grants with bbox coordinates
- transmitters: site rows from bundle
- exclusions: exclusion zones from bundle
- bands: frequency band specifications

Each index-grants for the same seed increments load_generation even when the bundle name changes.
