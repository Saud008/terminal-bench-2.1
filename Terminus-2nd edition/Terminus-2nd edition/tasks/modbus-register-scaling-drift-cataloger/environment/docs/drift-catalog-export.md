# Drift catalog export

export writes /app/output/drift-catalog.json after catalog_generation is greater than zero

## Preconditions

export refuses when catalog_generation in /app/state/catalog-generation.json is zero.

export recomputes frames_digest from poll-staging.json frames and must match stored frames_digest before publishing.

## Entry fields

Each catalog entry includes frame_id, device_id, register, raw, engineering, baseline, drift, drift_alarm, suppressed, scale_epoch.

drift = abs(engineering - baseline[register]).

drift_alarm = drift > drift_threshold unless suppressed.

## catalog_digest

Lowercase hex sha256 of the export JSON object with catalog_digest field removed, keys sorted recursively, compact encoding with no spaces.

## Rejected frames

rejected-frames.jsonl holds one compact JSON object per line for stale_device_clock rejections during catalog.
