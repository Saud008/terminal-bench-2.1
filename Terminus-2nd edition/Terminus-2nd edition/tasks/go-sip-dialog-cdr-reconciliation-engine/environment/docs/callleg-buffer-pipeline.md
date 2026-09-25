# Dialog buffer pipeline

ingest-transcript writes /app/state/dialog-buffer.json with tenant, scenario, messages, policy, dialog_seal.

compile-dialogs adds dialogs map keyed by branch key with answer_ts_ms, end_ts_ms, disposition, answered flag.

rate-billing adds billing_tier per dialog and writes billing-window-report.json.

TB3_FIXTURE_DIR may point at /opt/verifier-fixtures/sipcdrctl for hidden scenarios.
