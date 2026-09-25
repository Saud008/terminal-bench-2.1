# Calendar normalization

OnCalendar expressions use two tokens: day-spec and HH:MM:SS.

Supported day-spec forms:

- *-*-* for daily
- Mon..Fri for weekday ranges with Monday as day 0
- *-*-DD for monthly on day DD

Apply the effective Timezone timer key when converting local scheduled instants to UTC. When Timezone is absent, use host_timezone from the plan context.

Expand slots in the half-open interval (last_trigger_utc, reference_now] for missed-run detection.
