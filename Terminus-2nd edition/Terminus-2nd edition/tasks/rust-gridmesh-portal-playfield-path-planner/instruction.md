Portal playfield path puzzle

Build the portal playfield path puzzle, an offline square-grid tactics playtest planner for portal-linked board routing on the working baseline under /app. The planner loads playfield board packs, applies seeded portal jump scoring, audits bidirectional portal and off-mesh jumps, counts 4-connected walkable zones, and seals validate or path playtest exports when the win condition is met. This is a games playfield playtest and tactics board-routing workflow: keep Q16.16 board costs, linear snap and region invariants, walkable-zone scoring, playfield-staging snapshots, and sealed validate/path win-condition exports aligned. It is not a generic Rust CLI engineering, navmesh library rebuild, debugging, or CI tooling exercise.

navmeshctl is available at /usr/local/bin/navmeshctl. Subcommands and flags are cataloged in /app/docs/playfield-board-catalog.md and /app/docs/games-playtest-workflow.md:

  validate
  path

Board JSON grammar, cells, edges, portals, and off-mesh jump rows follow /app/docs/mesh-format.md. Bidirectional link audits, linear snap radius, region match, and 4-connected walkable-zone counting follow /app/docs/validate-contract.md. Validate and path export field shapes and playtest win conditions follow /app/docs/spec.md. Playtest workflow verbs and staging paths follow /app/docs/games-playtest-workflow.md.

validate reads --mesh and --seed, writes a playfield-staging snapshot under /app/state/playfield-staging/, and seals a validate export JSON at --export. path reads --mesh, --seed, --from, and --to, and seals a path export JSON at --export with status, cost_q16, and ordered cell ids.

Bundled playfield boards live under /app/fixtures/meshes/, with board inventory and seeds in /app/fixtures/catalog.json and /app/fixtures/seeds.json. Board overlays honor TB3_MESH_DIR per /app/docs/playfield-board-catalog.md. Run /app/scripts/reset-state.sh before cross-run verifier cases. The scout_decoy A* helper stays outside the validate and path playtest hot path. Do not modify /app/docs/, /app/fixtures/, or /tests/.
