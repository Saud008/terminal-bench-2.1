After merge coalesces internal nodes, recompute high_key to the maximum key in the merged subtree. When building a merged internal node, derive high_key from the merged children instead of reusing the left operand high_key field.

scan-range uses high_key to skip subtrees entirely below the query start. Inclusive scan-range after merge-heavy deletes must match filtering full export to the same start and end bounds.

Use /app/fixtures/delete_heavy.batch.jsonl to validate export, leaf_count, and scan-range locally before publish: after batch+publish, committed export must equal applying that JSONL under the tree-contract batch and underflow rules, walk leaf_count must match the resulting tree shape, and scan-range --start k03 --end k09 must equal filtering that export to the same bounds. Hidden verifier overlays under /opt/verifier-fixtures may reuse the same put/delete shape with different key prefixes; the merge high_key and underflow rules above still apply.
