Build the geo filter playfield puzzle, an offline map-window turn planner for rectangular filter playtest simulation on the working baseline under /app. The planner loads level packs, scores document tokens against window rulecards, and seals a playtest atlas from the scored round ledger.

geoboxplay is available at /app/bin/geoboxplay. Subcommands and flags are cataloged in /app/docs/planner-cli-catalog.md and /app/docs/level-catalog.md:

  load-level
  score-round
  seal-atlas

load-level materializes a salted level roster for a named pack under the level-roster schema. score-round ranks tokens under replica lag turn caps, floor quorum rulecards, and affinity rank rulecards, writing the round-score schema (including rounds where every document is denied). seal-atlas always writes the playtest atlas JSON named in /app/docs/playtest-atlas-contract.md from the current round-score ledger and must exit 0 with a successful atlas write even when admitted_count is 0. Rulecards for windows, token pins, lag caps, floor quorum, and affinity ranking live under /app/docs/, with playfield state paths and exit/output rules in /app/docs/playtest-rules-contract.md and /app/docs/planner-cli-catalog.md, and bundled packs under /app/fixtures/levels/ (paris-core is the primary playfield). Window scoring, token pins, replica lag caps, floor quorum, and affinity ranking each have their own rulecard under /app/docs/. Affinity line precision follows TB3_PLAY_DIGITS (default 4), token pin salting follows TB3_PLAY_SALT, alternate level roots follow TB3_LEVEL_DIR, and hidden overlays may appear under /opt/verifier-fixtures/geobox. The scout_decoy decoy stays outside the load-level, score-round, and seal-atlas playtest path. Do not modify docs/, config/, or fixtures/. Offline only.
