# Stop timeout driver

When stop exec begins, Monit must wait stop timeout seconds before start or restart exec may run. Restart requests that arrive earlier are deferred until stop_started_t plus stop_timeout.

The export boolean stop_timeout_respected is false when any restart or start request arrives at time t while a stop is in progress and t is strictly less than stop_started_t plus stop_timeout_sec, even if restart_exec is deferred to stop_started_t plus stop_timeout_sec. A deferred restart_deferred step still means stop_timeout_respected is false. The flag is true only when no restart or start request arrives before that boundary during an active stop window. Allowing restart or start uses current_t >= stop_started_t plus stop_timeout_sec (not merely current_t > stop_started_t).

Timeline steps include stop_begin and restart_deferred or restart_exec with t values respecting the timeout boundary.
