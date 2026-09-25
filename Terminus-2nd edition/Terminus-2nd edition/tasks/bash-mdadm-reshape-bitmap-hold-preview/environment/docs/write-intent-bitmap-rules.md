# Bitmap gate contract

If an array's `bitmap` field is `internal` or `external`, the array is blocked with reason `blocked_bitmap` unless `bitmap_clear_planned` is `true`.

A `bitmap` value of `none` never blocks, regardless of `bitmap_clear_planned`.

An array with `bitmap_clear_planned: true` and `bitmap` equal to `internal` or `external` is not blocked by this gate; the operator has already scheduled the bitmap to be cleared before the reshape begins.
