# Duplicate-prefix precedence

When multiple feeds supply feed-cache records for the same normalized prefix key, those records share one atlas row for that key. The winning country, asn, and winning_feed come from the record whose feed_id is lexicographically smallest. Distinct normalized prefix keys always produce separate overlap_rows even when their address spans nest; nested lengths do not compete for a single winner slot.
