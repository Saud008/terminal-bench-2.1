# Registry YAML format

Each fixture directory contains one `registry.yml` with a top-level `entries` list.

## Entry fields

| Field | Required | Description |
|-------|----------|-------------|
| `slug` | yes | Unique identifier within the merged registry (duplicates may appear; see contract). |
| `runner` | no | Runner id string, or YAML null when inherited from dependencies. |
| `requires` | no | List of slugs this entry depends on (may be empty). |
| `prefix` | no | Relative path under `/app` for the wine prefix (only on playable roots). |
| `dxvk_pin` | no | Semver constraint (`>=X.Y.Z`) checked against transitive `provides.dxvk_version`. |
| `provides` | no | Map of provided versions; only `dxvk_version` appears in fixtures. |

Example:

```yaml
entries:
  - slug: game-root
    runner: null
    requires:
      - shim-pack
    prefix: prefixes/active/stellaris
    dxvk_pin: ">=2.3.0"
  - slug: shim-pack
    runner: null
    requires:
      - dxvk-bundle
  - slug: dxvk-bundle
    runner: null
    requires:
      - wine-staging
    provides:
      dxvk_version: "2.3.2"
```

Paths are always relative to `/app`. Use forward slashes.
