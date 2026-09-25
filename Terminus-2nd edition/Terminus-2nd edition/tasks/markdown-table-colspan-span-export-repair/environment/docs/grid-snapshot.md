# Grid snapshot contract

After parse and grid placement, mdtable export persists the logical table model before writing export files.

## Path

Fixed path: /app/state/grid.snapshot.json (overwrite on every successful export run).

## Pipeline flow

1. Parse the pipe table block and decode colspan/rowspan markers.
2. Place cells on the logical grid with occupancy tracking.
3. Write the grid snapshot with column_count and rows.
4. Publish JSON or HTML from the snapshot only — do not re-parse the Markdown input during publish.

mdtable publish --export PATH --format json|html performs step 4 only.

## Schema

```json
{
  "version": 1,
  "export": {
    "export_version": 1,
    "source": "/app/fixtures/tables/example.md",
    "column_count": 4,
    "rows": [
      {
        "row_index": 0,
        "cells": [
          {"text": "Merged", "col": 0, "colspan": 2, "rowspan": 1}
        ]
      }
    ]
  }
}
```

Publish must copy snapshot column_count and cell spans into export output without recomputing grid width from raw cell counts.

Missing snapshot must cause publish to fail with non-zero exit.
