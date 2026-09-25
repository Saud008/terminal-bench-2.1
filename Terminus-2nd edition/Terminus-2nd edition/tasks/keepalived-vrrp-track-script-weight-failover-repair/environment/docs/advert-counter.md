# Advert counter

While role is MASTER, advert_seq increments by one after each processed event timestamp advance (one advert per event batch step).

When role changes from MASTER to BACKUP because a track weight demoted effective priority below master_threshold, advert_seq resets to 0.

Advert counter does not reset on BACKUP to MASTER promotion.
