# Prune traversal

Directory paths that resolve to transfer exclude on first match are pruned. Pruned directories are listed with prune true in compiled state.
Simplified behavior for this task: if a directory path is excluded by first match, do not descend into deeper children.
