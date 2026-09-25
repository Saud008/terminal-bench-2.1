# BGP UPDATE accrual rules

Track advertised, suppressed, penalty, flap_count, peak_penalty, last_ts_ms, stable_at_ms per peer and prefix.

announce when already advertised: no penalty change.

announce when suppressed and penalty at or above reuse_threshold: reject install.

withdraw when not advertised: no-op.

withdraw when advertised: clear advertised, add flap_penalty capped by max_penalty, increment flap_count, maybe set suppressed.

Do not add flap_penalty on announce.

After the event's announce or withdraw mutation (and peak update), if the slot is still not advertised and penalty is below reuse_threshold, set stable_at_ms to that event's ts_ms if unset. Evaluate the withdrawn check on post-event state only -- do not stamp from pre-event withdrawn status. An announce that installs the route leaves advertised true, so that event does not set stable_at_ms even when decay left penalty under reuse_threshold.
