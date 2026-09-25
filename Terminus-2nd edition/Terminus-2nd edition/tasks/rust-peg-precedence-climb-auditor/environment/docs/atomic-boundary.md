# Atomic boundary

Rules whose rhs is atomic wrap an inner pattern that must match without backtracking past the starting token index.

When matching atomic inner patterns, pestctl climb parse must attempt the atomic match before expanding any left_recursive rule alternative at the same cursor position.

If atomic matching fails after a partial inner match, the parser records an error_recovery span node, backtracks the cursor to the atomic start index, and does not treat the partial match as consumed input.

Left_recursive expansion is forbidden at a position until atomic alternatives for the current rule have been tried.
