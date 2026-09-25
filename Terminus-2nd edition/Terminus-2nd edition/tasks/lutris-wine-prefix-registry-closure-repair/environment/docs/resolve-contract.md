# Resolve contract

The resolver reads `registry.yml` from `--registry-dir`, merges duplicate slugs, walks the transitive `requires:` closure from `--root-slug`, and writes a JSON plan.

## Duplicate slug merge

When multiple entries share a `slug`:

- Merge their `requires` lists (union, deduplicated, sorted ASCII).
- Merge `provides` maps; conflicting values for the same key make the merge fail (record error, exit `2`).
- If runners differ and are not both null/empty, merge fails (exit `2`).
- On successful merge, append warning `duplicate slug <slug> merged`.

Later YAML entries must not silently overwrite earlier ones.

## Transitive closure

Collect every slug reachable from `--root-slug` following `requires` edges, including nested dependencies at any depth (fixtures include chains at least four levels deep).

Emit `closure` as dependency-first topological order: every required slug appears before its dependents. Tie-break equal-depth slugs by ascending ASCII slug.

Detect directed cycles among required edges. On cycle, set `closure` to `[]`, record cycle participants in `cycles`, exit `2`.

## Runner inheritance

The root entry may omit `runner` (null). Walk the merged `closure` in dependency-first order; the resolved runner is the **last** non-null, non-empty `runner` field encountered. If none is found, record error `missing runner for <root-slug>` and exit `1`.

Do not read only the root entry's `runner` field.

## Prefix canonicalization

When the root entry defines `prefix`, resolve it to an absolute path under `/app`:

1. Join `prefix_root` from config (default `/app`) with the relative `prefix`.
2. Follow every symlink hop to the real directory (use physical path resolution, not logical dirname).
3. Emit the canonical absolute path with no trailing slash.

Resolution must follow the full symlink chain to the physical directory path.

## DXVK semver pin

When the root entry sets `dxvk_pin`, locate `provides.dxvk_version` from any slug in the closure (first in dependency-first order wins). Compare using numeric semver components, not ASCII string ordering. Only `>=` constraints appear in fixtures.

On mismatch, record `dxvk pin <pin> not satisfied by <version>` and exit `1` when `fail_on_dxvk_mismatch` is true.

## Missing required slug

If any `requires` entry references a slug not present in the merged registry, record `missing slug <slug>` and exit `1` when `fail_on_missing_slug` is true.

## Config (`/app/config/resolve.json`)

- `prefix_root` (string): base for relative prefix paths (default `/app`).
- `fail_on_missing_slug` (boolean): default `true`.
- `fail_on_dxvk_mismatch` (boolean): default `true`.

## Determinism

Identical registry bytes, root slug, and config produce identical JSON output.
