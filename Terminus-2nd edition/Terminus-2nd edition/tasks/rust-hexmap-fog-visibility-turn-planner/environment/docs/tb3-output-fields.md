# Atlas field contract

Path: `/app/output/<run-id>-fog-atlas.json`

```json
{
  "run_id": "r1",
  "board_id": "plains-01",
  "fog_generation": 1,
  "target_reveal": 6,
  "visible_count": 7,
  "visible_cells": [{"q": 0, "r": 0}],
  "win_condition_met": true
}
```

`visible_cells` must be sorted by ascending `q`, then ascending `r`. `win_condition_met` is true when `visible_count >= target_reveal`.
