# Online offline parity

After independent point-in-time joins for offline and online sources, compare values rounded to three decimal places using standard half-away-from-zero rounding.

Values match when rounded offline equals rounded online. Otherwise parity_rows record match_ok zero with reason value_mismatch.

Missing online or offline selection yields reason missing_side.
