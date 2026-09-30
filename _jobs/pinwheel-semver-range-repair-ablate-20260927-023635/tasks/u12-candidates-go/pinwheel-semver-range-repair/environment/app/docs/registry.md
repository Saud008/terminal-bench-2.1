# Registry and manifest files

## Registry

A registry is a directory with one `NAME.json` file per package:

```json
{
  "name": "alpha-kit",
  "versions": [
    {
      "version": "2.3.1",
      "published": "2024-04-18T09:12:00Z",
      "yanked": false,
      "dependencies": { "beta-tools": "^0.4.0" }
    }
  ]
}
```

- `version` is a full version (`ranges.md`); a version string may appear only
  once per file.
- `published` is an RFC 3339 timestamp and is required.
- `yanked` defaults to `false`; `dependencies` defaults to `{}`.
- Releases do not have to be listed in version order. Their order in the file
  only matters for the last tie-break in `resolution.md`.

Unknown fields make the file invalid.

## pin.json

```json
{
  "name": "storefront",
  "dependencies": { "alpha-kit": "^2.0.0" },
  "overrides": { "beta-tools": "0.4.x" },
  "prefer": "highest"
}
```

- `name` is required.
- `dependencies` and `overrides` map package names to ranges; both are
  optional. Every range must be valid.
- `prefer` is `"highest"` (the default) or `"lowest"`.

Unknown fields make the file invalid.
