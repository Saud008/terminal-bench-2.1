# Table export JSON schema

```json
{
  "export_version": 1,
  "source": "/app/fixtures/tables/example.md",
  "column_count": 3,
  "rows": [
    {
      "row_index": 0,
      "cells": [
        {
          "text": "Header",
          "col": 0,
          "colspan": 1,
          "rowspan": 1
        }
      ]
    }
  ]
}
```

- `rows` sorted by ascending `row_index`.
- Within each row, `cells` sorted by ascending `col`.
- `text` is marker-stripped cell content.
- `column_count` is the grid width per the placement rules in `/app/docs/table-extension-contract.md`.

## CLI behavior

```bash
mdtable export --input PATH --export OUT --format json|html
```

- Exit `0` when export succeeds.
- Exit non-zero when `--input` is missing, unreadable, or contains no pipe table.
- Exporting the same input twice with the same `--export` path must produce byte-identical JSON output.
