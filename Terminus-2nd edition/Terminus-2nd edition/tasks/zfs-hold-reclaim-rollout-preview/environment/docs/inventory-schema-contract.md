# Inventory schema contract

Scenario path: `$fixture_dir/<scenario>/inventory.json` where `fixture_dir` defaults to `/app/fixtures/scenarios` and may be overridden by environment variable `TB3_FIXTURE_DIR`.

Required top-level fields:

- `pool` (string)
- `free_pct` (number)
- `floor_pct` (number)
- `datasets` (array of dataset objects)
- `bookmarks` (array of bookmark objects)

Optional:

- `focus_snapshots` (array of snapshot name strings)

Dataset object fields:

- `name` (string)
- `kind` (`filesystem` or `snapshot`)
- `depth` (integer)
- `creation_txg` (integer)
- `holds` (array of strings; may be empty)
- `clone_of` (string or null; filesystem clones reference a snapshot name)

Bookmark object fields:

- `name` (string)
- `target` (snapshot name string)

## Hold-name salt

Effective salt is environment `TB3_HOLD_SALT` when set and non-empty; otherwise config `hold_name_salt`. When the effective salt is non-empty, every string in each dataset `holds` array is rewritten to `hold + salt` at load time. Fixture inventories store unsuffixed hold names.

## load_seq

`/app/state/inventory.json` must include integer `load_seq`. When no inventory file exists at load time, `load_seq` is `1`. When an inventory file already exists, the new inventory's `load_seq` is the previous value plus one. `run-meta.json` must echo `scenario`, `run_id`, and `load_seq`.
