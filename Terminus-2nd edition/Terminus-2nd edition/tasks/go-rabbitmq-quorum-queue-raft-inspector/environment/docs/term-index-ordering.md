# Term and index ordering

Replay sorts entries by ascending index first within a term file scan, but global ordering must use (term, index) lexicographic ascending before state application.

When two entries share an index across terms, higher term wins for election records only after sort stabilization.
