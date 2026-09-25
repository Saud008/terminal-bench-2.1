Hard dependencies form a directed acyclic graph. For each dep CHILD hard PARENT edge, PARENT must appear before CHILD in plan order.

validate must exit 0 when the hard-dep graph is acyclic and exit 2 with stderr cycle:NODE,NODE,... when a directed cycle exists. Cycle detection belongs on validate, not only on export.

plan writes JSON with bundle and order fields. order lists every service exactly once. Lexicographic sorting of service names is not a valid plan when hard edges exist.

Topological tie-breaking among ready nodes uses ascending lexicographic service name.

Wants-only or soft edges never participate in cycle detection or plan ordering.
