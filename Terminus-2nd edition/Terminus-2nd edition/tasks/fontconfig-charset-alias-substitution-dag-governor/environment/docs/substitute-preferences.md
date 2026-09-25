# Substitute preferences

Family substitution blocks:

```xml
<substitute family="serif">
  <prefer>DejaVu Serif</prefer>
  <prefer>Liberation Serif</prefer>
  <prefer>FreeSerif</prefer>
</substitute>
```

## Order

`<prefer>` entries appear in **document order**. The first listed family has highest preference; the export `preferred` array preserves that order left-to-right.

Reversing the list changes match priority and fails contract tests.

## Lookup

Match `family` attribute case-sensitively against the `--family` CLI argument. Missing substitute blocks yield an empty `preferred` array (not an error).
