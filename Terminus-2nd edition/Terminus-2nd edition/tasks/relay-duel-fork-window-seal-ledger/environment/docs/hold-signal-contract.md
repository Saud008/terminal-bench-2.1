# Hold responses

Status codes 100, 180, 183 are hold. Match is answered only after first 2xx response to CHALLENGE.

Hold signals 180/183 must not set answer_ts_ms. Only status 200-299 mark accept.
