# Font reject rules

Rejection is declared with empty elements:

```xml
<reject-bitmap/>
<reject-outline/>
```

| Element | Effect |
|---------|--------|
| `<reject-bitmap/>` | Bitmap (non-outline) fonts are rejected |
| `<reject-outline/>` | Outline fonts are rejected |

These flags are **independent**. Setting one does not imply the other.

## Export fields

| Field | Type | Meaning |
|-------|------|---------|
| `reject_bitmap` | bool | true when `<reject-bitmap/>` present |
| `reject_outline` | bool | true when `<reject-outline/>` present |
| `font_kinds_allowed` | string[] | Subset of `"bitmap"`, `"outline"` still permitted |

Compute `font_kinds_allowed`:

- Neither tag → `["bitmap", "outline"]`
- Only reject-bitmap → `["outline"]`
- Only reject-outline → `["bitmap"]`
- Both → `[]`

Do not conflate bitmap and outline rejection into a single flag.
