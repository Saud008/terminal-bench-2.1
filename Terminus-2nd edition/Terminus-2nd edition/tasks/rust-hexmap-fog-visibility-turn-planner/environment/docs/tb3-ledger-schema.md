# Fog mask ledger schema

Path: `/app/work/fog-mask/<run-id>.json`

```json
{
  "run_id": "r1",
  "fog_generation": 1,
  "visible_cells": [{"q": 0, "r": 0}]
}
```

`visible_cells` is the sticky revealed set, listed with `q` then `r` ascending. Before the first `reveal-fog`, this file may be absent; after reveal it always reflects the current sticky mask and turn clock.
