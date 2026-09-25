Build the playfield fog planner, a Rust offline tactics CLI for hex-map fog-of-war playtest simulation and round planning on the working baseline under /app. The planner loads a playfield board, places the unit roster, resolves line-of-sight raycasts across elevation blockers, reveals sticky reveal ledgers across rounds, and seals a playtest output snapshot with a playtest win condition.

Install the release binary per /app/docs/tb3-board-catalog.md with these subcommands (flags in the same catalog):

  load-board
  place-units
  resolve-los
  reveal-fog
  seal-atlas

Axial (q, r) spacing rules are in /app/docs/tb3-qaxis-rules.md. Elevation blockers and equal-elev peek behavior are in /app/docs/elevation-blockers.md. Hex line raycast policy is in /app/docs/tb3-ray-policy.md. Class observer ranges (scout, infantry, tower, default) are in /app/docs/observer-range-table.md. Sticky reveal ledgers are in /app/docs/tb3-sticky-ledger.md. Round-clock fog_generation rules are in /app/docs/tb3-gen-counter.md. Roster, ray ledger, reveal ledger, and output field shapes are in /app/docs/board-roster-schema.md, /app/docs/tb3-ray-ledger-schema.md, /app/docs/tb3-ledger-schema.md, and /app/docs/tb3-output-fields.md. Playtest win_condition_met semantics are in /app/docs/playtest-win-condition.md.

load-board reads --board JSON and writes /app/state/board-roster/<run-id>.json with fog_generation 0. place-units rewrites the roster unit list from the loaded board. resolve-los writes /app/work/los-rays/<run-id>.jsonl. reveal-fog persists sticky /app/work/fog-mask/<run-id>.json and increments fog_generation on the roster. seal-atlas writes /app/output/<run-id>-fog-atlas.json.

Bundled boards live under /app/fixtures/boards/. Board overlays honor TB3_BOARD_DIR per /app/docs/tb3-board-catalog.md. Compile with cargo build --release --locked from /app. Run /app/scripts/reset-playfield.sh before cross-run verifier cases. The scout_decoy A* helper stays outside the load-board, place-units, resolve-los, reveal-fog, and seal-atlas hot path.
