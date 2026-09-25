# Board roster schema

Path: `/app/state/board-roster/<run-id>.json`

```json
{
  "run_id": "string",
  "board_id": "string",
  "target_reveal": 0,
  "fog_generation": 0,
  "cells": [{"q": 0, "r": 0, "elev": 0}],
  "units": [{"unit_id": "u1", "q": 0, "r": 0, "class": "scout"}]
}
```

`load-board` creates the roster from a board JSON path. `place-units` refreshes the `units` array from the roster board snapshot so the playfield roster is ready for LOS and fog turns.
