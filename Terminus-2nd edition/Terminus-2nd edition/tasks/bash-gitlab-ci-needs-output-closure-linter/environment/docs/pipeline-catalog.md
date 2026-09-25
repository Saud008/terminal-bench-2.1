# Pipeline catalog

matrix-basic exercises build to test to deploy needs with artifact paths.
matrix-duplicate contains permuted matrix axes that must canonicalize to one instance name.
rules-never applies merge request never rule before on_success fallback.
optional-needs declares a missing optional job that must not fail the graph.
stage-violation includes a test stage job needing a deploy stage producer.
artifact-chain requires transitive artifact path closure across three stages.

Verifier bundled scenarios use pipeline names matrix-basic, matrix-duplicate, rules-never, optional-needs, stage-violation, artifact-chain with run ids run-alpha, run-bravo, run-charlie, run-delta. Bundled YAML paths include /app/fixtures/pipelines/matrix-basic.yml and /app/fixtures/pipelines/rules-never.yml. Hidden overlay pipelines ship under /opt/verifier-fixtures/gclint/pipelines. Work files use paths such as /app/work/run-alpha-ingest.json and outputs such as /app/output/run-alpha-reexport.json.
