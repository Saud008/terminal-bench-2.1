# Pytest verifier primitives

Independent pytest modules under `/tests` may import `hashlib`, `math`, and `sqlite3` to recompute closure certificates and inspect `/app/state/plate-closure.db`.

`closure_spec.py` implements the laboratory reference math for FITS card parsing, pixel projection, epoch nudge, residual binding, and `closure_digest` normalization using `hashlib` and `math`.

`plate_session.py` wraps subprocess calls to `/app/bin/platclosectl` and reads `/app/state/bind-pass.json`, `/app/work/residual-matrix/<scenario>.jsonl`, and `/app/output/<scenario>-closure-certificate.json`.

`/app/support/verifier_math.py` mirrors the hashlib and math primitives used by verifier reference code.

Hidden verifier scenarios load from `/opt/verifier-fixtures/platclosectl/scenarios` when `TB3_FIXTURE_DIR` is set. Match-radius overrides use `TB3_MATCH_ARCSEC`.
