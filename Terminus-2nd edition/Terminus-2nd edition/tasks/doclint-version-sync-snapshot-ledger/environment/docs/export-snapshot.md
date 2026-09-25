# Snapshot export schema

Command: `workspace/executeCommand` with `"command": "doclint.exportSnapshot"` and `"arguments": ["<uri>"]`.

Response `result` object:

```json
{
  "uri": "file:///app/fixtures/sources/example.dlint",
  "version": 3,
  "text": "<flushed utf-8 text>",
  "diagnostics": {
    "todo_count": 0,
    "paren_delta": 0,
    "wide_char_lines": 0,
    "total": 0
  },
  "staging_pending": 0
}
```

`staging_pending` must be **0** after export (flush clears staging). Diagnostic fields follow `/app/docs/diagnostics-recompute.md`.
