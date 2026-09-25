# Merge contract

When multiple fragments contribute attributes for the same block, attribute maps merge in fragment source order (lowest order value first).

Nested object keys must deep-merge on collision. If fragment A sets tags.Name and fragment B sets tags.env, the merged result must retain both keys. Replacing the entire tags object from a later fragment is incorrect.

merge_override maps apply after base attribute merges from all fragments. An explicit null literal in merge_override removes or nulls that attribute key in the merged result. Null is a real value and must not be treated as absent or skipped.

Dot notation in staging (for example tags.env) expands to nested objects in the normalized export JSON.
