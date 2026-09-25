# Experiment manifest

Each experiment directory under /app/fixtures/experiments/<name>/ contains:

- `examples.jsonl` — one JSON object per line with fields `example_id`, `as_path` (list of ASN ints, origin last), `peer_group` (string), `label` (0 or 1 for non-leak / leak).
- `relationships.json` — map of `"asn_a|asn_b"` to one of `customer`, `provider`, `peer`. Directed: key `A|B` = A is customer/provider/peer of B.
- `model.json` — `{"weights": [...], "bias": float, "feature_names": [...]}` matching the feature vector order in aspath-feature-vector.md.

routeleaklab evaluate loads the experiment, derives features, standardizes using training-group statistics only, scores every row, selects a threshold on the validation split, evaluates the test split, writes /app/state/eval-snapshot.json, then seals the model-card report.
