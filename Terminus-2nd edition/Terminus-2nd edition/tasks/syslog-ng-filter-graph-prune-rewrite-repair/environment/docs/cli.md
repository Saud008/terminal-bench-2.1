# CLI surface

syslogctl replay --config-dir PATH --messages PATH --seed STRING --export PATH [--reload full|partial]

All paths are absolute. Missing arguments exit code 2.

replay resets working state via /app/scripts/reset-state.sh except preserved cache files when reload allows reuse.
