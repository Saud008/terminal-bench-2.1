# Platform rubric — university-degree-audit-exception-engine

**Task folder:** tasks/university-degree-audit-exception-engine/

Agent loads scenario SQLite into registrar-workspace.db via load-scenario, +2
Agent materializes transcript-staging.json with independent staging fingerprint digest, +3
Agent locks catalog year from scenario metadata without inflating from course rows, +3
Agent maps transfer enrollments through articulation equivalence year windows, +3
Agent rejects substitutions expired before the audit term boundary, +3
Agent folds repeat enrollments keeping highest grade per course code, +3
Agent rolls satisfied child requirement credits into parent closure nodes, +3
Agent honors registrar exception waivers when evaluating requirement rows, +2
Agent publishes degree-audit-report.json only when evaluation-pass audit_pass is positive, +2
Agent sorts published requirement rows by req_id ascending in the matrix export, +2
Agent increments audit_pass counter in evaluation-pass.json on each run-audit, +2
Agent keeps decoy honorroll module off the publish-report hot path, +1
Agent rebuilds degaudit via verifier-rebuild.sh before verifier pytest, +1
Agent publishes audit matrix without a successful run-audit pass gate, -3
Agent selects catalog year as max course catalog year instead of locked scenario year, -3
Agent keeps first repeat enrollment grade instead of highest retake grade, -3
Agent applies substitution rows after their expires_after_term boundary, -3
