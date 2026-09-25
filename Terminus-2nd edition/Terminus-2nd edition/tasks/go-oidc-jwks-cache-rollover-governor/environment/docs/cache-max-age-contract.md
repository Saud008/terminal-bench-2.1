# Cache max-age

cache_max_age_sec from the final timeline event is measured in seconds.

Reject with cache_stale when last_timeline_epoch minus signature_epoch exceeds cache_max_age_sec for active key acceptance.
