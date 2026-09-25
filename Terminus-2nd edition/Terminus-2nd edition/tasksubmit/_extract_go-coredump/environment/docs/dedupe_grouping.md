# Duplicate crash grouping

Duplicate crashes share a `group_key` computed as lowercase hex SHA-256 over the concatenation of:

- uppercase build ID of the **top frame** after authenticity admission (empty string if unresolved)
- decimal signal number
- symbol name of top frame (empty if unresolved)
- basename of the top frame module

All crashes with the same group_key belong to one group. Groups export sorted by `group_key` ascending.
