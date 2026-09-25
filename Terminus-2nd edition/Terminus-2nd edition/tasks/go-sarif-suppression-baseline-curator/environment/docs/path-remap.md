# Path remap

Remap runs on every finding URI before dedupe, suppression, and baseline comparison.

## Order

1. Normalize backslashes to forward slashes.
2. Apply prefix_strip entries longest match first (sort by length descending).
3. Apply rewrite map entries longest key first, replacing the first matching prefix.

4. Trim one leading forward slash if present after prefix_strip and rewrite.
