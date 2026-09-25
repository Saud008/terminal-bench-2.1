# Stale device clock

Each frame carries received_ms (gateway receive time) and device_clock_ms (device-reported time).

## Skew limit

Use device.clock_skew_ms from manifest unless a per-register override clock_skew_ms is set.

## Rejection

Reject the frame when abs(device_clock_ms - received_ms) > skew limit.

Rejected frames append one JSON line to /app/output/rejected-frames.jsonl with reason stale_device_clock. Rejected frames are not catalog entries.
