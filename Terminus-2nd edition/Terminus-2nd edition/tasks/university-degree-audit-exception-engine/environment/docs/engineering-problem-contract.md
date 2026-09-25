# Engineering problem contract

degaudit solves academic degree progress evaluation, not ML experiment provenance curation or HPC module load planning.

Reasoning path:

1. Lock catalog year from scenario_meta before any course eligibility check.
2. Correlate transfer enrollments through articulation equivalence windows keyed by catalog year.
3. Apply substitution waivers that expire after a stated academic term boundary.
4. Fold repeat enrollments by retaining the highest grade_points per course_code.
5. Topologically sort requirement nodes and use induction from leaves toward the program root while backtracking when grade floors fail.
6. Cascade satisfied credits from child requirement nodes to ancestors after direct matches are proved.
7. Reconcile registrar exception waivers into per-node satisfied totals without breaking graph invariants.
8. Infer satisfied booleans by ranking grade_points and deducing min_credits shortfalls per node.

Distinct artifacts: transcript-material.json fingerprint, requirement-eval.json evaluation rows, degree-audit-report.json requirement matrix.

Distinct constraints: grade floor C or better, catalog_year_introduced filter, articulation inclusive year bounds, substitution term expiry, exception waiver credits.
