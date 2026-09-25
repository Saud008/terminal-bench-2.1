# Reconnect ledger schema contract

Compile writes `/app/state/reconnect-ledger.json` with:

- `run_id` (string)
- `scenario` (string)
- `load_seq` (integer)
- `fleet` (string)
- `cutover_window_min` (number)
- `eligible` (array of `{adapter_id, mac, salted_id, criticality, gatt_service_count, reconnect_attempts, rank}`, sorted per reconnect-rank-rules.md)
- `ineligible` (array of `{adapter_id, mac, reason}`, sorted by `adapter_id` ascending then `mac` ascending)
- `eligible_count` (integer)
- `ineligible_count` (integer)

## reason ladder

When multiple gates would block the same device, record a single `reason` using this ladder (first matching wins):

1. `ineligible_pairing_required`
2. `ineligible_resume_armed`
3. `ineligible_power_sequence`
4. `ineligible_reconnect_storm`
