# Validation report schema

Output: `/app/output/validation-report.json` — UTF-8 JSON, pretty-printed with two-space indent and a trailing newline.

## Top-level object

| Field | Type | Description |
|-------|------|-------------|
| `seed` | string | Copied from config `seed` |
| `payloads` | string[] | Payload filenames selected for this run, in validation order |
| `results` | array | One result object per entry in `payloads`, same order |
| `stats` | object | Aggregate counts for the selected payloads |

## `stats`

| Field | Type | Description |
|-------|------|-------------|
| `validated` | integer | Number of payloads processed |
| `valid` | integer | Count of results where `valid` is `true` |
| `invalid` | integer | Count of results where `valid` is `false` |

## `results[]`

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Payload filename (matches the parallel `payloads` entry) |
| `operation` | string | Operation key from the payload envelope (`METHOD /path`) |
| `valid` | boolean | Whether `data` satisfies the dereferenced request-body schema |
| `errors` | string[] | Empty when `valid` is `true`; otherwise one message per validation failure |
| `cycles_seen` | integer | Number of `$ref` cycles detected while dereferencing this payload's schema |

## Error message formats

When `valid` is `false`, each `errors` element must be a single string using **exactly** one of these templates (placeholders are the property name, key, or discriminator value involved):

| Condition | Message template |
|-----------|------------------|
| Required property absent (no default) | `missing required {name}` |
| Discriminator property present but not in `mapping` | `unknown discriminator {value}` |
| Unknown key when `additionalProperties` is `false` | `additional property {key}` |
| JSON `null` on a non-nullable property | `{field} cannot be null` |
| Wrong JSON type | `{field} must be string`, `{field} must be integer`, or `{field} must be object` |
| Schema could not be resolved | `missing schema` |

Integer validation accepts JSON numbers (including values unmarshalled as floating-point).

## Example

```json
{
  "seed": "oas-seed-6",
  "payloads": ["valid-cat.json"],
  "results": [
    {
      "file": "valid-cat.json",
      "operation": "POST /pets",
      "valid": true,
      "errors": [],
      "cycles_seen": 0
    }
  ],
  "stats": { "validated": 1, "valid": 1, "invalid": 0 }
}
```
