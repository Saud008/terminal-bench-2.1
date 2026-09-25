# Notify barrier

Role transitions set notify_pending true. The notify hook at /app/scripts/notify_transition.sh must finish before export.

Staging field notify_complete becomes true only after the hook writes /app/state/notify.done.

Export to /app/output/vrrp-state.json must not occur until notify_complete is true for the final staging snapshot. If no role transition occurred, notify_complete may remain true from initialization.

Also write /app/state/export-ready with the basename of the output file after durable publish.
