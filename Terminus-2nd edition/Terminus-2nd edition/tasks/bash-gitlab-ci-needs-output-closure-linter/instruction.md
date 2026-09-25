Build gclint, a GitLab CI pipeline linter on the working Bash baseline under /app. The tool ingests GitLab CI YAML from /app/fixtures/pipelines/, writes an expanded job graph snapshot at /app/state/gclint-staging.json, and emits a deterministic lint report JSON to a caller-provided path under /app/output/.

Install gclint at /app/bin/gclint with these subcommands:

  gclint ingest --pipeline <name> --run-id <id>
  gclint analyze --run-id <id>
  gclint export --run-id <id> --output <path>

Pipeline YAML layout and bundled inventory appear in /app/docs/pipeline-catalog.md. Matrix job expansion and duplicate instance detection follow /app/docs/matrix-expansion-contract.md. Rules evaluation order and when values follow /app/docs/rules-precedence-contract.md. Stage ordering constraints for needs edges follow /app/docs/stage-ordering-contract.md. Required versus optional needs semantics follow /app/docs/needs-optional-contract.md. Artifact path closure across needs chains follows /app/docs/artifact-closure-contract.md.

gclint analyze materializes the staging snapshot for a run id. Staging schema, digest fields, and expanded job records appear in /app/docs/staging-snapshot-schema.md. gclint export reads the staging snapshot only and writes lint findings plus summary counters to the caller-provided output path. Export row ordering and audit_digest rules appear in /app/docs/lint-export-fields.md.

Bundled pipelines live under /app/fixtures/pipelines/. Pytest helpers in tests/gclint_cli_support.py invoke gclint through subprocess. Independent contract math lives in tests/gclint_contract_math.py. Run /app/scripts/reset-state.sh before cross-run verifier cases. The merge_rules_helper decoy module is not on the ingest or export hot path.
