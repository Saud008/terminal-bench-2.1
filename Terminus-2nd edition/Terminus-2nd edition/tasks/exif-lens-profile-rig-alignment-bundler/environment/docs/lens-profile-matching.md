# Lens profile matching

Lens profiles catalog rows include lens_id, focal_mm, profile_revision, and effective_capture_ms.

For a capture with normalized_ms, select the profile where:

- lens_id matches capture lens_id
- effective_capture_ms <= normalized_ms
- effective_capture_ms is maximal among matching rows

If no profile matches, reject capture with reason missing_lens_profile in rejected-captures.jsonl.
