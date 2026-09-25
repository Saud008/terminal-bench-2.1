# Fixture catalog

Bundled fixtures under /app/fixtures:

| File | Role |
|------|------|
| scans/alpha.sarif.json | Primary SARIF scan |
| snapshots/alpha-snapshot.json | Prior snapshot fixture |
| policies/alpha-policy.json | Suppression policy with alias and expired window |
| remap/ci-paths.json | CI path prefix strip |
| catalog.json | Verifier seeds map |

Hidden gamma corpus ships under /opt/verifier-fixtures/sarif-gamma when TB3_FIXTURE_DIR is unset.
