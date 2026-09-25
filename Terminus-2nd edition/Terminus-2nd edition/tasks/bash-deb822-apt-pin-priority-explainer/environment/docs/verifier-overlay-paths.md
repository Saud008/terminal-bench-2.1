# Verifier overlay paths



Cross-run verifier cases copy hidden scenario trees from /opt/verifier-fixtures/debpol/scenarios/ into /app/work/tb3-root/<scenario-name>/ before invoking debpol build-policy with TB3_SCENARIO_ROOT set to /app/work/tb3-root.



Build-policy also writes /app/work/<run-id>-policy-build.json for each run id.



Standard pytest output paths use /app/output/<run-id>-candidates.json unless a test names a custom export path under /app/output/.

