# Trackgraph zone reachability contract

Track adjacency edges are undirected. For each anchor block B, the protected zone is the undirected reachability set of B over adjacency: B plus every block reachable by walking adjacency edges any number of hops.

Direct neighbors alone are insufficient when possessions or reservations sit on blocks separated by one or more edges. Diamond and fork yards require full reachability.

The zone_map value for each anchor must list block_id strings sorted ascending lexicographically.

Optional TB3_ZONE_SALT appends the salt string to each participant id only when building group participant keys for emit, not when computing zone_map reachability sets.
