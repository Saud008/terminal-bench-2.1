# Ledger stack schema

pamtrace-ledger.json contains run_id, scenario, services map, outcomes, subjects, ledger_fingerprint.

Each services entry includes service name, modules array of expanded auth modules in execution order, and service_fingerprint as sha256 of modules JSON.

ledger_fingerprint is sha256 of JSON object mapping service name to service_fingerprint plus run_id.
