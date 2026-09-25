# Readings format

Path: user-supplied TSV beside ingest --readings

Lines beginning with # and blank lines are ignored. A header row whose second column is the literal L is ignored.

Fields are tab-separated:

| Column | Name | Type |
|--------|------|------|
| 1 | patch_id | string |
| 2 | L | float |
| 3 | a | float |
| 4 | b | float |
| 5 | batch_id | string optional |

When the same patch_id appears on multiple lines, the last line in file order wins.
