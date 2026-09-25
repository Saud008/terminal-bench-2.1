# Policy graph schema

deb822-policy-graph.json includes run_id, scenario, target_arch, origins, preferences, package_rows, queries, origin_fingerprint, graph_digest.

graph_digest hashes run_id, origin_fingerprint, and sorted package name, version, origin_id tuples in package_rows using hashlib sha256 over canonical JSON.
