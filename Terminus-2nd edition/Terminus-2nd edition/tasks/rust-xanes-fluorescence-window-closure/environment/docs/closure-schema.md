# Closure schema

Success:

```json
{
  "status": "ok",
  "trace_id": "...",
  "windows": [
    {
      "window_id": "...",
      "element": "...",
      "edge_code": "...",
      "integral": 0.0,
      "channels_sorted": ["..."]
    }
  ],
  "all_channels_sorted": ["..."],
  "closure_digest": "<sha256 hex>"
}
```

`all_channels_sorted` lists every channel across the window tree in spectroscopic rank order (see `edge-ordinal-table.md`).

`closure_digest` is SHA-256 of compact JSON (separators `,` and `:`) of the list
`[{"window_id":...,"integral":...}, ...]` sorted by `window_id`.

Error: `{"status":"error","message":"..."}` and process exit code 1.
