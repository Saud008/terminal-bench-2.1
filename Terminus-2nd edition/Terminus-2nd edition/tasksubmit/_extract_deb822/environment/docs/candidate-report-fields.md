# Candidate report fields

debpol candidate-report reads deb822-policy-graph.json only. install_candidates array sorts by package name ascending. Each row includes package, chosen_version, origin_id, effective_priority, verdict.

Export writes to any caller-provided absolute path under /app/output/, including re-export paths such as /app/output/run-alpha-reexport.json and export smoke paths such as /app/output/run-export-report.json used by cross-stage verifier cases.

audit_digest is sha256 of the install_candidates JSON array canonical form.

Default export filename pattern: /app/output/<run-id>-candidates.json. Custom re-export paths include /app/output/run-alpha-reexport.json and /app/output/run-export-report.json.
