# Pytest verifier primitives

Bundled pytest uses hashlib.sha256 hex digests when recomputing atlas_fingerprint from species_rows and landing_audit JSON.

Contract helpers live in tests/quota_atlas_verifier.py alongside the fqrctl subprocess driver.
