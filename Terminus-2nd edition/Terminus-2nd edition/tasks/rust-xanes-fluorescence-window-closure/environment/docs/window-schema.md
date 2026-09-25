# Window schema

```json
{
  "windows": [
    {
      "window_id": "w1",
      "element": "Fe",
      "atomic_number": 26,
      "edge_code": "K",
      "e_lo": 7100.0,
      "e_hi": 7200.0,
      "channels": ["fe-kα", "fe-kβ"],
      "children": []
    }
  ]
}
```

Nested scopes use `children`. An `edge_code` beginning with `?` denotes an undeclared edge marker and must error.
