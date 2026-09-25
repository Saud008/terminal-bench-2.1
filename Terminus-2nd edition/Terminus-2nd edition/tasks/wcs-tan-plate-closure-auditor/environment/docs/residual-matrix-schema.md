# Residual matrix schema

`bind-residuals` writes `/app/work/residual-matrix/<scenario_id>.jsonl`.

Line 1 is a header object:
`{"type":"residual-matrix","scenario_id":"<id>"}`

Example matrix-buffer files include `plate-tight-tan.jsonl`, `plate-repeat-seal.jsonl`, and `plate-multi-star.jsonl` under `/app/work/residual-matrix/`.

Example certificate filename: `plate-repeat-seal-closure-certificate.json` under `/app/output/`.
`{"star_id":"...","delta_ra_arcsec":...,"delta_dec_arcsec":...,"sep_arcsec":...}`

Numeric fields use fixed six-decimal formatting. Rows are sorted by `star_id`.
