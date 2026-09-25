# Fixture catalog

Bundled offline repository fixtures under /app/fixtures/repos/:

| repo_id | path | purpose |
|---------|------|---------|
| baseline | /app/fixtures/repos/baseline | checksum verification, dual widget lineage, module defaults |
| lineage | /app/fixtures/repos/lineage | EVRA ordering trap with sortable-pkg versions 10.1 vs 9.99 |

Each repo includes repodata/repomd.xml, repodata/primary.xml, repodata/modules.yaml, and mirror-snapshot.json. baseline also ships mirror-stale.json for negative mirror validation experiments.

Hidden verifier repositories may appear under /opt/verifier-fixtures/repos/ with distinct package names. Tests may set TB3_PACKAGE_SALT to mutate expected package rows at runtime.
