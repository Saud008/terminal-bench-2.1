# Pidfile hygiene

Programs may declare pidfile path. After unclean kill (process gone but pidfile still present), Monit must unlink the stale pidfile before the next start exec.

The export field pidfile_stale_at_start is true when start exec ran while the pidfile still contained a dead process token from a prior unclean kill without clearing.

Successful hygiene sets pidfile_stale_at_start false for that replay.
