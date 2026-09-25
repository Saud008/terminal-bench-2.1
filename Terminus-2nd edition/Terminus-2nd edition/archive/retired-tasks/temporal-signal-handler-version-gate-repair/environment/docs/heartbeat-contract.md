# Heartbeat clock

Activity heartbeat offsets in the staging snapshot use **server** timestamps (`heartbeat_server_ms` from the scenario).

Do not record `worker_time_ms` in `heartbeat_offset_ms`.

Export sets `heartbeat_clock_source` to `"server"`.
