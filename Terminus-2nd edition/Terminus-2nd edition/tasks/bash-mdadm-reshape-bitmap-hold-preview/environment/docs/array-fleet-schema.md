# Inventory schema contract

Scenario path: `$fixture_dir/<scenario>/inventory.json` where `fixture_dir` defaults to `/app/fixtures/scenarios` and may be overridden by environment variable `TB3_SCENARIO_DIR`.

Required top-level fields:

- `fleet` (string)
- `host_salt` (string)
- `window_hours` (number)
- `spare_holds` (array of device name strings)
- `arrays` (array of array objects)

Array object fields:

- `name` (string)
- `level` (string; current RAID level, e.g. `raid1`, `raid5`, `raid6`, `raid10`, `raid0`)
- `target_level` (string; requested RAID level after reshape)
- `active_disks` (integer)
- `spares` (array of device name strings; may be empty)
- `bitmap` (string; one of `none`, `internal`, `external`)
- `bitmap_clear_planned` (boolean)
- `estimated_hours` (number)
- `criticality` (integer)

## Host salt and salted_name

At scan time, every array is assigned `salted_name`, computed as the first 16 hex characters of `sha256(host_salt + ":" + name)`, using the inventory's own `host_salt` field. Fixture inventories store their own `host_salt`; scan does not accept a salt override.

## load_seq

`/app/state/inventory.json` must include integer `load_seq`. When no inventory file exists at scan time, `load_seq` is `1`. When an inventory file already exists, the new inventory's `load_seq` is the previous value plus one. `run-meta.json` must echo `scenario`, `run_id`, and `load_seq`.
