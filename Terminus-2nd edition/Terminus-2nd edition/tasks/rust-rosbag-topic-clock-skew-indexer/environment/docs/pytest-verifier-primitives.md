# Pytest verifier primitives

Tests invoke /app/bin/skew-cal via subprocess after cargo rebuild. Shared harness fixtures live in tests/conftest.py. Independent reference math lives in tests/temporal_sync_oracle.py using Python statistics and hashlib only.

Pytest plugin modules test_c8skew_cli_surface, test_c8skew_manifest_lane, test_c8skew_message_lane, test_c8skew_atlas_emit, and test_c8skew_verifier_overlays partition behavioral probes.

Bundled rover field log identifiers rover-alpha, rover-beta, rover-gamma, and rover-delta appear in /app/docs/fixture-bag-catalog.md.
