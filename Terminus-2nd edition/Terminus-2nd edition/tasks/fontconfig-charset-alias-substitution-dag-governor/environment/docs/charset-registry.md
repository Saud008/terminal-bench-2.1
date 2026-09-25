# Charset registry

Charset entries use:

```xml
<charset name="ISO8859-1:1987" short="iso8859-1" encoding="8859-1">
  <alias ref="latin-core"/>
</charset>
```

| Field | Meaning |
|-------|---------|
| `name` | Full registry key (unique) |
| `short` | Human shorthand; may repeat across different full names |
| `encoding` | Encoding label carried by this charset node |
| `alias ref` | First hop of alias expansion |

## Lookup

Resolution queries use the **`name`** attribute exactly. Basename extraction (`ISO8859-1` from `ISO8859-1:1987`) or short-name indexing is wrong when multiple charsets share a revision prefix or short tag.

Two charsets with the same `short` but different `name` values are **distinct** entries. Merging or overwriting by `short` alone loses charset variants.

## Duplicate short names

Valid configuration may contain:

- `ISO8859-1:1987` / `short="iso8859-1"` / `encoding="8859-1"`
- `ISO8859-1:1998` / `short="iso8859-1"` / `encoding="8859-1-rev2"`

Both must remain addressable by full `name`.
