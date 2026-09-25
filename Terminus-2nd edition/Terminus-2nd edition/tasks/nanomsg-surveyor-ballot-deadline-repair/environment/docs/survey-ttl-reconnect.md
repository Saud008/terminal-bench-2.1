Each respondent receives default_ttl_ms from mesh start offset. ExpiresMS is start offset plus default_ttl_ms unless reconnect resets the window.

reconnect at offset R sets ttl_expires_ms to R plus default_ttl_ms for that respondent. reconnect_reset on the event is true when the window was reset.

Ballot events after ttl_expires_ms must set reject_reason ttl_expired and must not stage votes.
