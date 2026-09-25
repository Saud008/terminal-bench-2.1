# Manifest overrides

Per-register entries in register_overrides keyed by register address string.

Supported override fields:

| Field | Effect |
|-------|--------|
| word_order | Replaces default_word_order for decode |
| scale_epoch | Pins scale epoch_id for that register |
| clock_skew_ms | Replaces device clock_skew_ms for stale check |

Overrides apply before decode, epoch selection, and stale clock rejection for that frame.
