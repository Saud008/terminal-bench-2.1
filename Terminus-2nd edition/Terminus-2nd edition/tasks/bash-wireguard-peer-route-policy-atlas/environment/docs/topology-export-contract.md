# Topology export

Export reads the workspace snapshot only. peers array includes only active peers sorted by public_key ascending. overlaps and route_conflicts copy from the workspace snapshot. audit_digest is sha256 of deterministic JSON array [peers, overlaps, route_conflicts].

        Verifier helpers write export output to /app/output/{run-id}-atlas.json. Examples include /app/output/run-stable-atlas.json and /app/output/run-decoy-atlas.json.
