# Conflict precedence

When two loaded modules declare a conflict (either direction), the module with higher @priority remains loaded. The lower-priority module is moved to the unload sequence before the winner loads.

Tie-breaking:
- Equal priority conflicts are resolved by lexicographic module name (smaller name wins)

Unload ordering:
- Conflict evictions appear in unload_sequence in the order they are displaced
- A module skipped because it lost a conflict never appears in load_sequence
