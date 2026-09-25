# pkctl — polkit-style rule evaluation sandbox

Offline polkit decision simulator used by platform automation. See /app/docs/polkit-evaluation.md for the evaluation contract.

Commands:

- pkctl evaluate --scenario PATH
- pkctl merge-rules --stack NAME
- pkctl lookup-action --action-id ID

State directories:

- /app/output — last evaluation JSON per run
- /app/state/auth-cache.json — implicit authorization cache (cleared by reset-state.sh)
