# Rotation epoch window

Given bundle_epoch and window W from TB3_ROT_WINDOW or default 5:

An identity rotation_epoch is kept when min <= rotation_epoch <= max where min = bundle_epoch - W and max = bundle_epoch.

When rotation_epoch is absent, last_seen_epoch is used for the window check only.

Bounds are inclusive on both ends.
