# Merge metadata

Merging splits combines document postings and metadata catalogs. Rules:

1. Invalidate hot-cache entries for both source splits before removing them from split-meta.json.
2. Remove source split rows from the metadata catalog only after cache invalidation succeeds.
3. Create merged split with split_id equal to the lexicographically smallest source split UUID string.
4. Record merge-audit.json with cache_flushed true when both source caches were invalidated.

If either source split is unknown, merge returns an error and must not mutate manifest or checkpoint.

Hot cache must not serve documents from splits removed from split-meta.json.
