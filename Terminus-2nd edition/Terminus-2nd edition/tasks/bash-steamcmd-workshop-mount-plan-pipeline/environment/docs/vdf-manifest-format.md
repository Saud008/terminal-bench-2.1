# Workshop VDF manifest format

Each fixture epoch supplies a `manifest.vdf` in Valve KeyValues (VDF) text form.
`/app/lib/vdf_parse.sh` reads it into declaration-ordered TSV before staging.

## Structure

```
"WorkshopCollection"
{
	"mods"
	{
		"<mod_id>"
		{
			"version"	"<version>"
			"depends"
			{
				"<target_mod_id>"
				{
					"version"	"<constraint>"
					"optional"	"0"
				}
			}
		}
	}
}
```

- The root object is `WorkshopCollection`; the mod map lives under `mods`.
- Each mod has a `version` string and an optional `depends` map.
- Each dependency entry carries a `version` constraint and an `optional` flag
  (`"0"` = required, `"1"` = optional).

## Parsed TSV rows

The parser preserves manifest declaration order and emits tab-separated rows:

- `MOD\t{mod_id}\t{version}`
- `DEP\t{from_mod}\t{to_mod}\t{constraint}\t{optional}`

`from_mod` is the dependent mod that declared the `depends` block, and `to_mod`
is the dependency target. A mod's own `MOD` row is emitted before the `DEP` rows
for the dependencies it declares.

## Version constraints

Constraints use a numeric operator prefix over a dotted version:

- `>=X.Y.Z`, `>X.Y.Z`, `<=X.Y.Z`, `<X.Y.Z`, `==X.Y.Z`
- A bare `X.Y.Z` is treated as `>=X.Y.Z`.

Comparisons are **numeric**: each dotted component is compared as an integer, so
`1.10.0` satisfies `>=1.2.0`. Lexical (ASCII) string comparison is incorrect.
