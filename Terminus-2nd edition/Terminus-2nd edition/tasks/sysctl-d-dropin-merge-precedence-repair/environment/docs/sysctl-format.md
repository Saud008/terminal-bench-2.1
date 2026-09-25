# Sysctl fragment format

Lines are trimmed. Empty lines and lines whose first non-whitespace character is `#` are ignored.

Inline comments begin at the first unescaped whitespace followed by `#`; strip the comment and trailing whitespace from the assignment portion only. Values may contain `#` when it is not preceded by whitespace.

Assignments accept either `key = value` or `key value` (single whitespace or tab between key and value). Keys must match `^[a-z0-9][a-z0-9_.-]*$` and contain at least one dot.

Invalid keys or malformed lines make `apply` fail with a non-zero exit code.

## Value normalization (`/app/lib/normalize.sh`)

`build_snapshot` normalizes parsed assignment values through `normalize_value` before storing them in snapshot `effective` (and therefore in apply export). Parse output keeps the raw token from the file; normalization runs during merge.

When a value is wrapped in paired ASCII double quotes, strip the outer quotes and replace each `\"` sequence inside with a literal `"`. Values without paired outer quotes are stored exactly as parsed (including interior `#`, tabs, and spaces).

## Drop-in ordering (`/app/lib/order.sh`)

`compute_drop_in_order(tree, seed)` returns manifest `drop_ins` sorted by ascending hex `SHA-256` of UTF-8 bytes `seed + ":" + relative_path`, where `relative_path` is each manifest entry verbatim. Ingest calls this function from `build_snapshot`; `drop_in_order` in `tree.sh` is not used on that path.

