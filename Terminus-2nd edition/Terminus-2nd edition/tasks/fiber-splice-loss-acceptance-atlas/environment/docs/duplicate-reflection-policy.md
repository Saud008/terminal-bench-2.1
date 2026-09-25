# Duplicate reflection policy

Bucket events by floor(distance_m / reflection_tolerance_m).
Within each bucket keep the event with the highest epoch.
Sort surviving events by distance_m ascending.
