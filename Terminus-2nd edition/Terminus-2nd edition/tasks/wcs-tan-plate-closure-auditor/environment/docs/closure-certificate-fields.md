# Closure certificate fields

Default output path: `/app/output/<scenario_id>-closure-certificate.json`.

JSON object fields (all required):

- `scenario_id`
- `matched_count` — accepted residual rows
- `active_count` — same as matched_count after quality gating at bind time
- `rms_ra_arcsec` — RMS of `delta_ra_arcsec` over active rows, half-up to 6 decimals
- `rms_dec_arcsec` — RMS of `delta_dec_arcsec`, half-up to 6 decimals
- `closure_class` — `tight` when both RMS values are `< 0.35`, else `loose`
- `stars` — sorted active `star_id` list
- `closure_digest` — SHA-256 hex of normative UTF-8 digest bytes:

`{"scenario_id":"<id>","active_count":N,"star_ids":["..."],"rms_ra_arcsec":0.000000,"rms_dec_arcsec":0.000000}`

Digest payload rules: compact JSON, keys in that exact order, `star_ids` sorted ascending,
RMS numbers printed with exactly six digits after the decimal point, `scenario_id`
JSON-string-escaped.
