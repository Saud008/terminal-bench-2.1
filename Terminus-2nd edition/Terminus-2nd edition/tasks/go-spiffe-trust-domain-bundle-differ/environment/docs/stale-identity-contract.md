# Stale identity detection

Stale threshold is 3 epochs.

Drop x509_svid entries when last_seen_epoch < bundle_epoch - stale_threshold.

Keep entries at or above bundle_epoch - stale_threshold.
