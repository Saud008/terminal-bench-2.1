# Keepalived config subset

config-check parses a minimal keepalived vrrp_instance block listing track_script names. Each name must map to a track in /app/config/vrrp.json and the script path must exist. config-check executes each script once and records exit_code in the report.

Report path fields: tracks_checked, scripts_run, all_scripts_ok.
