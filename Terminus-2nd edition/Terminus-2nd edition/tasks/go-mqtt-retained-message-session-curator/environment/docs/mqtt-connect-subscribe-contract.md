# MQTT connect and subscribe contract

CONNECT events establish client_id and clean_session flags. SUBSCRIBE events register topic filters before any PUBLISH is evaluated. On SUBSCRIBE, the broker must evaluate retained messages immediately for matching topics and queue atlas rows before offline delivery replay begins.

Filters are literal paths or use MQTT single-level plus and multi-level hash wildcards per /app/docs/wildcard-match-contract.md. A SUBSCRIBE with filter plant/temp/# must not match unrelated branches such as plant/humidity/room1 when only plant/temp/1 is published.

Disconnect events close the session window; offline QoS deliveries after DISCONNECT obey /app/docs/session-expiry-contract.md.
