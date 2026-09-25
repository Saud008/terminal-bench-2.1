# Missing frame accounting

Mount inventory defines expected_frames_per_slot and frame_index_start.

For each rig slot, expected frame indices are the inclusive range:

```
frame_index_start .. frame_index_start + expected_frames_per_slot - 1
```

After align accepts captures for a slot, any expected index without an aligned capture is listed in missing_frames on align-generation.json and bundle-manifest.json.
