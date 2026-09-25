# Verifier harness contract

Pytest rebuilds seismocomply from the current /app tree through the session autouse fixture in /tests/conftest.py before any subprocess CLI invocation.

Reference exceedance math lives in /tests/seismocomply_contract_math.py using hashlib, math, and random for anti-hardcode overlay surveys.

CLI fixture helpers live in /tests/seismocomply_cli_support.py. Hidden survey tb3-night-scale and seed tb3-scale load from /opt/verifier-fixtures/seismocomply/surveys when TB3_FIXTURE_DIR is set.
