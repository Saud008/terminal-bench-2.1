# Predicate allowlist

After trust bind, an envelope is predicate-eligible only when its `predicate_type` exactly equals one entry in the merged allowlist (no glob, no substring).

Merged policy packs **union** predicate allow entries. If the merged allowlist is empty, every trusted envelope fails predicate checks.

Terminal deny reason when no trusted envelope is predicate-eligible: `predicate_reject`.
