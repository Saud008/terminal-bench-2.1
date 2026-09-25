# OpenAPI offline validation contract

## Payload selection

Config `/app/config/oasctl.json` supplies `seed` and `payloads`.

1. **Bitmask select** — Let `digest = sha256(seed)`. Use the first two bytes of `digest` as a 16-bit bitmask over the config `payloads` list (only the first sixteen entries are considered). Include filename `payloads[i]` when bit `i` is set.
2. **Non-empty fallback** — If no filenames are selected, include exactly one entry: `payloads[digest[2] mod len(payloads)]`.
3. **Order shuffle** — Fisher–Yates shuffle the selected list in place using `digest[i mod len(digest)] mod (j+1)` as swap indices (same algorithm as `OrderPayloads` in the reference implementation).

The report's `payloads` array and `results` array use this final order. `stats` counts only the selected payloads.

## Dereference pipeline

Request-body schemas are resolved before validation:

1. **$ref chains** — Follow internal `#/components/schemas/Name` references to a fully expanded schema.
2. **Cycle detection** — Track active refs on the stack. When a ref is revisited, stop expanding that branch and treat the node as an empty object schema (record one cycle for the validation result).
3. **allOf merge** — Resolve each subschema, then merge properties. When the same property appears in multiple fragments, **later** fragments override earlier ones. Required arrays are unioned.
4. **Discriminator** — After base resolution, when the payload contains the discriminator property, use `mapping` to select the subschema and merge it onto the base. Unknown mapping values are validation errors.
5. **Default injection** — Apply `default` values from properties **after** allOf merge and discriminator merge, filling missing properties in the working schema used for validation.

## Nullable unions

A property typed as `[string, "null"]` (or any type list containing `null`) accepts JSON `null`.

## Validation

- Required properties must be present in the payload `data` object (unless the merged schema supplies a `default` for that property).
- Types are checked after dereference (including nullable unions).
- When `additionalProperties` is `false`, unknown keys in `data` are errors.
- Validation failures must populate `errors` using the message templates in `/app/docs/report-schema.md`.
