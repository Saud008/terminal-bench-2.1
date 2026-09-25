# Playfield board catalog

Bundled playfield boards live under /app/fixtures/meshes/. The inventory is /app/fixtures/catalog.json and seeds are /app/fixtures/seeds.json.

Hidden verifier boards copy to /opt/verifier-fixtures/playmesh/meshes/ (includes mesh_id tb3-diagonal-trap and tb3-portal-pin). When TB3_MESH_DIR is set, tests resolve overlay board paths from that directory instead of /app/fixtures/meshes/.

The scout_decoy sandbox under /app/scout_decoy/ is not on the validate or path playtest hot path.
