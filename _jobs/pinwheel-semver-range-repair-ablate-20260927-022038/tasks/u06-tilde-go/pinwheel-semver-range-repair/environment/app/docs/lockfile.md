# pin.lock

`pin.lock` is written next to `pin.json`. It is JSON in UTF-8 with this exact
layout, so that locks diff cleanly in review:

- two-space indentation, one member per line, a single trailing newline;
- object members in the order shown below, `packages` and `dependencies`
  sorted by key (byte order);
- strings escaped only where JSON requires it, so `<`, `>` and `&` appear
  as-is.

```json
{
  "lockfileVersion": 1,
  "name": "demo",
  "packages": {
    "alpha-kit": {
      "version": "2.3.1+build.5",
      "requiredBy": [
        "<root>",
        "beta-tools"
      ],
      "dependencies": {}
    },
    "beta-tools": {
      "version": "0.4.0",
      "requiredBy": [
        "<root>"
      ],
      "dependencies": {
        "alpha-kit": ">=2.1 <3"
      }
    }
  }
}
```

| field | value |
|-------|-------|
| `lockfileVersion` | always `1` |
| `name` | the `name` from `pin.json` |
| `packages` | one entry per package in the final selection |
| `version` | the release's `version` string exactly as the registry lists it, build metadata included |
| `requiredBy` | the package's dependents, sorted, each listed once; the project is `<root>` |
| `dependencies` | the selected release's `dependencies` as listed in the registry, `{}` when it has none |
