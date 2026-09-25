# Implicit authorization cache

When evaluation yields result yes (implicit allow), pkctl stores an entry in /app/state/auth-cache.json before returning decision cached_allow on subsequent identical requests.

Cache key fields:

- action_id
- user
- seat

Different seat values must not share cache entries even when action_id and user match.

Cache hits return decision cached_allow, source cache, implicit true, and matched_rule null.

reset-state.sh clears the cache file to an empty object.

The cache is consulted only after rule and action resolution and after challenge handling determines an implicit yes outcome.
