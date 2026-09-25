# Pytest verifier primitives

Pytest rebuilds rotrace from /app sources before tests. Contract math lives in tests/brine_ndp_contract.py using hashlib only per this document. CLI helpers in tests/swro_pipeline_driver.py invoke subprocess on /app/bin/rotrace. Support helpers in /app/support/rotrace_pytest_helpers.py document TB3_FIXTURE_ROOT and TB3_CAL_TABLE overrides. Chronicle contract cases use tests/test_brine_chronicle_contract.py with isolated_swro_profiler from tests/conftest.py.
