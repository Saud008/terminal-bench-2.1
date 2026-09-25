# Interim interval precedence

When a Start packet attrs include both Session-Timeout and Acct-Interim-Interval, the effective interim flush interval for that session is Acct-Interim-Interval seconds.

Session-Timeout is the maximum session lifetime hint for the NAS; it must not replace Acct-Interim-Interval for proxy interim buffer timing.

When only Session-Timeout is present, use Session-Timeout as the interim interval. When neither attribute is present, use default_interim_interval_sec from /app/config/radiusproxy.json.
