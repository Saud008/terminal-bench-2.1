# Half-life decay

Before each event at time t:

delta_ms = t minus last_ts_ms

penalty = floor(penalty times 0.5^(delta_ms / half_life_ms))

Reuse-timer forecast ms_to_reuse uses integer half-life projection: floor(penalty_now * half_life_ms / (half_life_ms + delta_ms)). Invert for the smallest non-negative delta that places that value strictly below reuse_threshold as specified in /app/docs/reuse-timer-forecast.md.
