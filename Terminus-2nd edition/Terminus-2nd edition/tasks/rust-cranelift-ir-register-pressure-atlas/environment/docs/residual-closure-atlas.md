# Residual closure atlas

emit-occupancy writes pretty-printed JSON to the caller-provided `--output` path.
Verifier cases use paths under `/app/output/` such as `/app/output/{campaign}.json`,
`/app/output/iso.json`, `/app/output/idem1.json`, `/app/output/idem2.json`,
`/app/output/spill.json`, `/app/output/spill2.json`, `/app/output/scale.json`, and
`/app/output/nl.json`.

rows contain only non-vetoed channels, sorted by residual_counts descending, then
channel_id ascending. rank is 1-based in that order. Each row has channel_id,
residual_counts, rank, vetoed (always false in rows).

channel_order lists non-vetoed channel_ids in energy_q order (see
energy-order-lemma.md).

closure_digest is the lowercase hex SHA-256 of the atlas body -- every field except
closure_digest itself -- serialized as compact JSON with object keys in sorted
alphabetical order at every nesting level (matching Python's
`json.dumps(obj, sort_keys=True, separators=(",", ":"))`). The sealed atlas file
itself is pretty-printed with a single trailing newline; the digest is computed over
the compact canonical form, not the pretty form.
