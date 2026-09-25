# Coordinate transforms

Axes are defined in `axes.json` keyed by array name.

Each array entry contains:

- `dims` — ordered dimension names matching `shape` length
- `coordinates` — map from dimension name to coordinate metadata

Each coordinate entry has:

- `length` — must equal the corresponding `shape` entry at the same dimension index
- `transform.scale` and `transform.offset`

World coordinate for zero-based index `k`:

```
world(k) = offset + scale * k
```

`coordinate_span` for each dimension is `[min(world(0), world(length-1)), max(world(0), world(length-1))]`.

`transform_ok` is false when any coordinate length disagrees with its shape dimension.
