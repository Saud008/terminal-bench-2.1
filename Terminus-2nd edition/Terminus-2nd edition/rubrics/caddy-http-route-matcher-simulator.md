# Platform rubric — caddy-http-route-matcher-simulator

**Task folder:** tasks/caddy-http-route-matcher-simulator/

Agent selects winning route by specificity score instead of first array match, +3
Agent compiles path_regexp patterns with full-path anchors not substring containment, +3
Agent folds header names and values when case_sensitive is unset or false, +2
Agent stops route group evaluation at terminal routes without handle_path fallthrough, +3
Agent exports stable handler @id from staging instead of route index placeholder, +3
Agent reads staging snapshot and last-match for export without re-parsing route JSON, +2
Agent wires ingest to write caddy-stage.json and commit replay metadata, +2
Agent rebuilds caddyctl after editing matcher or export packages, +2
Agent ignores decoy wrap helper on match and export hot path, +1
Agent hardcodes route-handler.json without running caddyctl route export, -3
Agent fixes only path_regexp while leaving specificity ordering on array index, -2
Agent folds header names but compares header values case-sensitively, -2
Agent allows handle_path siblings after a terminal route match, -3
Agent writes route-index handler_id in export output, -2
