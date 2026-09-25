# Scene-pack playtest pack rules

## Inputs

Each scene pack under `/app/fixtures/trees/<name>/` contains:

- `tree.json` — file list, optional `delete_on_merge`, branch metadata
- `remap.json` — map of old UID string to new UID string
- Branch directories (`base`, `left`, `right`, …) holding `.tscn` files

Apply **seed playtest overlays** from `/app/fixtures/seeds.json` on top of each pack’s `remap.json` before resolving any branch copy. See the seed fields table below.

CLI `--base` names the branch whose content wins on packed-scene conflicts. Invokers (including automated checks) pass `--base` **already resolved**; apply must honor that branch name and must **not** re-apply `base_flip_seed_mod` during playtest resolution.

### Seed configuration (`/app/fixtures/seeds.json`)

| Field | Role |
|-------|------|
| `seeds` | Seed integers exercised against catalog scenarios |
| `catalog_seed` | Default seed for catalog scenarios that use a single seed |
| `base_flip_seed_mod` | Divisor for **callers** choosing which branch name to pass as `--base` |
| `remap_slot` | UID string the seed overlay adds or overwrites in the remap map |
| `remap_prefix` | Prefix for the generated overlay target UID |
| `remap_suffix_mod` | Integer divisor for the overlay suffix (see formula below) |

**Identity overlay formula:** when `remap_slot` is set, the overlay entry is

`remap[remap_slot] = {remap_prefix}_{seed % remap_suffix_mod}`

Example: `remap_prefix` = `uid://player_new`, `remap_slot` = `uid://player_old`, seed `7`, `remap_suffix_mod` `5` → `uid://player_new_2` (because `7 % 5 == 2`).

**Base branch selection (caller only):** before invoking apply, if `seed % base_flip_seed_mod == 1`, pass branch name `left`; otherwise pass branch name `base` from the scenario catalog. The apply command receives that branch name via `--base` and uses it directly for conflicts.

## UID identity overlay

Before branch resolution, apply `remap.json` (plus seed overlay) to **every** branch copy:

- Replace `uid="OLD"` tokens on `[ext_resource …]` and `[sub_resource …]` lines
- Replace `uid="OLD"` on the root `[gd_scene … uid="…"]` line when present
- Do **not** rewrite unrelated `path="res://…"` strings unless the UID token on the same line matches

## Packed-scene branch resolution

For each relative `.tscn` path listed in `tree.json`:

1. Load base, left, and right bytes (missing branch = empty).
2. If only one side changed, take that side.
3. If both sides changed identically, take either.
4. If both sides changed differently (**conflict**), take the **`--base` branch** version — never newer filesystem mtime.

Files listed in `delete_on_merge` are omitted from `merged_files` but still participate in orphan detection.

## UID graph

Build a directed graph of scene UIDs:

- Each resolved file contributes its root `[gd_scene … uid="…"]`
- Only `[ext_resource type="PackedScene" … uid="…"]` lines add an edge from the containing scene UID to the referenced UID
- Other `ext_resource` types (for example `Texture2D`, `Script`, `Shader`) must **not** add graph edges even when they carry a `uid="…"` attribute

Report `uid_graph_ok: false` and list `cycles` when any directed cycle exists. Each cycle entry is an ordered array of UID strings describing one directed loop (the first UID repeats at the end).

## Orphans

After resolution and deletes, any `uid="…"` reference in remaining resolved content must resolve to a root UID present in `merged_files`. Collect dangling references in `orphans`. For example, the orphan-trap catalog leaves `uid://enemy_old` referenced from `main.tscn` after `enemy.tscn` is deleted on resolve.

## Sealed playtest export JSON

Write pretty JSON with keys:

| Key | Meaning |
|-----|---------|
| `tree` | Absolute tree path |
| `base`, `left`, `right` | Branch names used |
| `seed` | Seed integer |
| `merged_files` | Map of relative path → resolved text (LF line endings) |
| `uid_graph_ok` | Boolean |
| `cycles` | Array of UID cycles (each cycle is an array of UID strings) |
| `orphans` | Array of `{file, uid}` objects |
| `ledger` | Object per ledger schema |

Normalize resolved file text to **LF** before storing in `merged_files`.

## Exit codes

See `/app/docs/exit-codes.md`.
