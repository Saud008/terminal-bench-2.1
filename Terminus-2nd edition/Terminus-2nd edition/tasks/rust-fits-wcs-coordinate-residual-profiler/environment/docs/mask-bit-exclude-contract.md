# Mask bit exclude contract

MASK_EXCLUDE is 0x02. A source is excluded when either detection mask_bit or catalog mask_flags has MASK_EXCLUDE set. Excluded sources remain in match rows with masked true but do not contribute to active_count or RMS fields.
