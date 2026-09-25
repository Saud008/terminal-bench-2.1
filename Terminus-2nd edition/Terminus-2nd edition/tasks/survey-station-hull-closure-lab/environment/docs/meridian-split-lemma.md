# Wrap partition lemma

After residual subtraction, scan consecutive residual vertices. If any absolute longitude
delta is strictly greater than 180, the ring wraps.

Wrapped rings split into west (residual lon >= 0) and east (residual lon < 0) parts.
Emit part station ids `<station_id>-W` and `<station_id>-E` only when that part has at least
three vertices. Non-wrapping rings keep the original station_id.
