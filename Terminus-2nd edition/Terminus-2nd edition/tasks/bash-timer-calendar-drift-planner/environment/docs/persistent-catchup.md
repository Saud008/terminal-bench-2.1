# Persistent catch-up

When Persistent=true, every missed calendar slot strictly after last_trigger_utc and on or before reference_now is listed in catchup_run_utc.

catchup_run_count is the length of catchup_run_utc.

When Persistent=false, catchup_run_utc is empty.

persistent_enabled reflects the merged Persistent timer key.
