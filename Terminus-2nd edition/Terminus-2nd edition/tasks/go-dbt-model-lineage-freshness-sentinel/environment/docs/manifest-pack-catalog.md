# Manifest pack catalog

Bundled packs under /app/fixtures/bundles/ exercise DAG shape, source freshness, disabled models, and exposure closure.

| Pack | Focus |
|------|-------|
| core-lineage | Simple enabled model chain |
| freshness-mixed | Sources spanning ok, warn, and error windows |
| disabled-refs | Enabled model depends on disabled upstream |
| exposure-depth | Exposure depends on model with transitive deps |
