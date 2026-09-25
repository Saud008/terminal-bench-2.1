# Message-ID deduplication

The scanner may find multiple Maildir files with the same `Message-ID` header.

## Winner selection

For each Message-ID cluster, keep exactly one file:

1. Higher `mtime_ns` wins.
2. On tie, prefer `cur/` over `new/` (cur rank 2, new rank 1).
3. On further tie, lexicographically greater relative path wins.

Losers are not indexed; increment `duplicates_merged` once per discarded file.

## Thread binding

All files in a cluster share one `thread_id` equal to the canonical thread root for that Message-ID graph. Duplicate copies must not fork separate threads.

Thread roots: walk `In-Reply-To` and `References` (angle-bracket tokens, left-to-right) to union messages; the root is the lexicographically smallest Message-ID in the component.

Export and SQLite `thread_id` values are that root Message-ID **verbatim** (including `<` and `>`). Do not prefix with `t-` or strip angle brackets.
