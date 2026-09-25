# Trace schema

```json
{
  "trace_id": "string",
  "points": [{"e_ev": 7100.0, "mu": 0.42}, ...]
}
```

Points must be processed in ascending `e_ev` order. Duplicate energies are allowed; stable sort by `e_ev` only.
