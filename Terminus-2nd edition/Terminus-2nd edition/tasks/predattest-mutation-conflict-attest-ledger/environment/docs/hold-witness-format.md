# Hold witness format

`compile` stages a compact witness at `/app/state/wavehold/hold-witness.json`
(pretty JSON, sorted keys) that binds to the atlas it was compiled from. It is
the subset operators diff quickly before pulling the full atlas.

```json
{
  "schema_marks": ["labels"],
  "applied_edits": 6,
  "held_records": 1,
  "held_attrs": ["drain_token"],
  "last_commit_index": 7,
  "atlas_digest": "<64 hex chars>"
}
```

Every field must equal the corresponding field of the compiled atlas, and
`atlas_digest` must equal the atlas's `atlas_digest` exactly. The witness
carries no `outcomes` or `nodes`; the digest is the binding to the full
atlas.
