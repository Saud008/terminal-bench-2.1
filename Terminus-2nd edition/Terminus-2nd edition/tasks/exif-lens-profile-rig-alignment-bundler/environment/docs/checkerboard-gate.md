# Checkerboard calibration gate

Checkerboard JSONL rows provide capture_id, board_detected boolean, and reprojection_error float.

Reject capture with calibration_failed when:

- board_detected is false, or
- reprojection_error is strictly greater than calibration_error_limit from bundler.json (default 0.5)

Checker rows missing for a capture_id are treated as passing.
