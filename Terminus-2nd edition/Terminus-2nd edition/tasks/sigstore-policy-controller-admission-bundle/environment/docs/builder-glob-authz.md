# Builder authz

Builder identity gates apply only to `pred_ok` envelopes: subject-digest matched, trust-bound, and predicate-eligible.

## Deny list

If any `pred_ok` envelope's `builder_id` matches a deny glob (full-string anchored `*`), the pull is denied with reason `builder_deny`. Deny uses the **union** of deny globs across merged packs.

## Require list

If the merged require list is non-empty, at least one `pred_ok` envelope must match a require glob. Later policy packs with a **non-empty** require list **replace** the prior require list entirely. Empty require lists in a later pack leave the prior list unchanged.

Miss yields reason `builder_require_miss`.
