# Verifier refmath contract

Pytest invokes mqttsessctl through mqttsess_cli.py subprocess helpers. mqttsess_refmath.py implements wildcard, retained, QoS, expiry, and export verifier math independent of Go sources. Staging digests use digest_util.py from /app/fixtures/digest_util.py. TB3_FIXTURE_DIR selects hidden journal roots under /opt/verifier-fixtures/mqttsessctl.
