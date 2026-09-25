Geo filter playfield puzzle

Build the geo filter playfield puzzle, a terminal offline turn planner for
Meilisearch-style rectangular filter playtest simulation on the working baseline
under /app. The planner loads level packs, scores document tokens against window
rulecards, and seals a playtest atlas when the win condition is met. Identity
token: d2c7f9a481.

Install /app/bin/geoboxplay from the planner scripts. Subcommands and flags are
cataloged in /app/docs/planner-cli-catalog.md and /app/docs/level-catalog.md.

load-level materializes a salted level roster for a named pack. score-round ranks
tokens under replica lag turn caps, floor quorum rulecards, and affinity rank
rulecards. seal-atlas writes the playtest atlas JSON named in
/app/docs/playtest-atlas-contract.md.

Rulecards for windows, token pins, lag caps, floor quorum, and affinity ranking
live under /app/docs/. Playfield state paths are listed in
/app/docs/playtest-rules-contract.md. Bundled level packs ship under
fixtures/levels/ (paris-core is the primary playfield).

Affinity line precision follows TB3_PLAY_DIGITS (default 4). Token pin salting
follows TB3_PLAY_SALT. Alternate level roots follow TB3_LEVEL_DIR.

Verifier helpers geobox_cli and geobox_authority ship beside the tests;
parallel reference math is under scripts/geobox_math.py. Hidden overlays live
under /opt/verifier-fixtures/geobox. Reset with scripts/reset-state.sh before
cross-run checks. The scout_decoy decoy is not on the load-level/score-round/
seal-atlas planner path.

Do not modify docs/, config/, or fixtures/. Offline only.
