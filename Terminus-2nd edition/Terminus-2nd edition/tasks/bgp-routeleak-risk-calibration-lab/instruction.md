Machine-learning operators preparing BGP route-leak risk scores must run routeleaklab on labeled AS-path experiment batches under /app/fixtures/experiments/. The lab builds feature vectors from AS-path dumps and peering relationships, runs linear-model inference, selects a decision threshold on a group-aware validation split, and writes an evaluation model-card report with calibration metrics for held-out test examples.

Install the CLI at /usr/local/bin/routeleaklab. Reported fields, feature definitions, split rules, threshold selection, and metric formulas must match the contracts under /app/docs/ for every bundled and hidden experiment.

Primary command:
  routeleaklab evaluate --experiment <name> --report <path>

Optional:
  routeleaklab evaluate --experiment <name> --report <path> --run-id <id>

Experiment directories are /app/fixtures/experiments/<name>/. Each directory holds examples.jsonl, relationships.json, and model.json. The optional env TB3_FEATURE_SCALE multiplies the standardized feature matrix when present; otherwise config key feature_scale in /app/config/routeleaklab.json applies. The CLI writes a staging snapshot to /app/state/eval-snapshot.json then the sealed model-card report to --report (default /app/output/routeleak_eval_report.json when omitted).

Read /app/docs/experiment-manifest.md, /app/docs/aspath-feature-vector.md, /app/docs/relationship-features.md, /app/docs/feature-standardization.md, /app/docs/stable-sigmoid.md, /app/docs/group-holdout-split.md, /app/docs/fbeta-threshold-search.md, /app/docs/confusion-brier-ece.md, /app/docs/model-card-report.md, /app/docs/cli-exits.md, and /app/docs/fixture-notes.md.

Independent contract math used by the verifier lives only under /tests (routeleak_contract_math.py and routeleak_support.py; hashlib is used there for audit_digest, matching /app/tools/audit_digest_ref.py). Do not modify /app/docs/, /app/config/, or /app/fixtures/. The decoy package routeleak_lab/decoy is not on the inference hot path.
