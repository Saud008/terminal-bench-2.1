# Parallel path isolation

In ring or dual-source layouts, multiple closed paths may energize a bus. When requires_isolation is set on a close step, the target bus must not already be energized before the close executes.

When parallel_path_guard is set on an open step, opening must be blocked if the breaker currently isolates an energized subsection from the rest of the yard.
