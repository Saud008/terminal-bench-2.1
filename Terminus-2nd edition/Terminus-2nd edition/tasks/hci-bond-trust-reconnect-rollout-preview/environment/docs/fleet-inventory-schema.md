# Fleet inventory schema contract

Scenario path: `$fixture_dir/<scenario>/inventory.json` where `fixture_dir` defaults to `/app/fixtures/scenarios` and may be overridden by environment variable `TB3_SCENARIO_DIR`.

Required top-level fields:

- `fleet` (string)
- `host_salt` (string)
- `cutover_window_min` (number)
- `adapters` (array of adapter objects)

Adapter object fields:

- `adapter_id` (string)
- `host` (string)
- `power_plan` (string; one of `cycle`, `off_first`)
- `devices` (array of device objects)

Device object fields:

- `mac` (string)
- `addr_type` (string; e.g. `public`, `random`)
- `bonded_addr_type` (string; the address type recorded at the original bond time)
- `trusted` (boolean)
- `pairing_confirmed` (boolean)
- `resume_token` (string; empty string when no cached resume key exists)
- `resume_cleared` (boolean)
- `disconnect_before_power` (boolean; only meaningful when the owning adapter's `power_plan` is `off_first`)
- `gatt_uuids` (array of GATT service UUID strings; may contain mixed-case duplicates)
- `battery_probes_ms` (array of integers; millisecond timestamps of low-energy battery probe events used as a reconnect-attempt proxy)
- `criticality` (integer)

## Host salt and salted_id

At scan time, every device is assigned `salted_id`, computed as the first 16 hex characters of `sha256(host_salt + ":" + adapter_id + ":" + mac)`, using the inventory's own `host_salt` field. Fixture inventories store their own `host_salt`; scan does not accept a salt override.

## load_seq

`/app/state/inventory.json` must include integer `load_seq`. When no inventory file exists at scan time, `load_seq` is `1`. When an inventory file already exists, the new inventory's `load_seq` is the previous value plus one. `run-meta.json` must echo `scenario`, `run_id`, and `load_seq`.
