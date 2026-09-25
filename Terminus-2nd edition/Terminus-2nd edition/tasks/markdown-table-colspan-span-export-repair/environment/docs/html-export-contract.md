# HTML export contract

Each placed cell becomes one `<td>`. The count of `<td>` elements per row must equal the number of cells in the JSON row model.

## Document shape

Write a single `<table>` root with one `<tr>` per grid row:

```html
<table>
  <tr>
    <td>...</td>
  </tr>
</table>
```

Requirements:

- Wrap all rows in `<table>` … `</table>`.
- End the file with `</table>` and a single trailing newline.
- Use one `<tr>` per JSON row, in the same order as `rows[]`.
- Emit one `<td>` per placed cell in that row, in left-to-right order.

## Cell attributes

- Emit `colspan="N"` when the placed cell `colspan` is greater than 1.
- Emit `rowspan="N"` when the placed cell `rowspan` is greater than 1.
- When both attributes apply, emit `colspan` before `rowspan`.
- Omit attributes whose value is 1.

Example:

```html
<td colspan="2" rowspan="3">Merged</td>
```

## Text escaping

Escape cell text for HTML:

| Character | Replacement |
|-----------|-------------|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |

Span marker syntax (`>N<`) must not appear in exported text; only the resolved grid cell text is written.

## Verification note

Exporters may vary insignificant whitespace between tags. Behavioral checks compare the parsed table model (row count, per-row td count, escaped text, and span attributes), not a raw byte-identical HTML string.
