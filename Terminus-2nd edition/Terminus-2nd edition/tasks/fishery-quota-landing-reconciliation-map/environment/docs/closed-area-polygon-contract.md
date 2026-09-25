# Closed-area polygon contract

Each closed area defines an axis-aligned bounding box and a closed date range inclusive on both ends.

A landing is inside a closed area when landed date is within closed_from and closed_until and lat/lon satisfy min_lat <= lat <= max_lat and min_lon <= lon <= max_lon.

Reject accepted landings with reject_reason closed_area:{area_id}.
