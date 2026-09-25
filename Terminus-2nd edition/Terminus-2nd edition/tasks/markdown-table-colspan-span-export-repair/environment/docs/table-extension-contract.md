# Table extension contract

Pipe tables are contiguous blocks of lines that start with `|`. Blank lines end a block. Only the first table block in a file is exported.

## Row parsing

- Split each row on unescaped `|` delimiters. A backslash immediately before `|` includes a literal pipe in the cell text (`a\|b` is one cell).
- Trim whitespace around each cell body after splitting.

## Alignment row

The row immediately after the header is an **alignment row** (not data) when every cell matches `^:?-+:?$` after trim. Skip it when building body rows.

## Span markers

After trim, cell text may include span markers:

| Marker | Position | Meaning |
|--------|----------|---------|
| `>N<` | prefix | colspan `N` (integer ≥ 1). Strip the marker from exported text. |
| `@N@` | suffix | rowspan `N` (integer ≥ 1). Strip the marker from exported text. |

Default colspan and rowspan are `1` when markers are absent.

## Grid placement

Body rows (header + alignment skipped) are placed left-to-right on a logical grid:

1. Skip column slots occupied by an active rowspan from earlier rows.
2. Place the next cell at the lowest free column index.
3. Mark `colspan × rowspan` slots as occupied starting at that column.
4. `column_count` is the maximum `(col + colspan)` across all placed cells.

Row indices in exports are 0-based body rows (header is row 0, first data row is row 1).
