Implement the caddyctl offline HTTP route matcher on the working Go baseline under /app. The tool ingests Caddy-style JSON route tables from a directory, writes a canonical normalized staging snapshot at /app/state/caddy-stage.json with commit metadata at /app/state/caddy-commit.json, simulates raw HTTP request bytes against staged matchers using deterministic ordering and specificity invariants, and exports the selected handler identity to the report file whose path is /app/output/route-handler.json

Your work must satisfy every contract cited below. The internal/decoy package is not on the match or export hot path and must not be edited for a correct export.

Build /app/bin/caddyctl from cmd/caddyctl. Subcommands:

  caddyctl ingest <routes-dir>
  caddyctl match --request <http-bytes-file>
  caddyctl route export

After ingest, /app/state/caddy-stage.json must list routes in source file order with matcher blocks, terminal flags, handle_path markers, and stable handler @id values copied from the JSON id field.

match reads the staging snapshot and raw HTTP request bytes (method line, headers, optional body). It writes /app/state/last-match.json with the winning handler @id. Matcher evaluation must follow /app/docs/matcher-specificity-order.md: among all matching routes, the highest specificity score wins; array index alone must not decide the winner when a more specific route also matches.

Path regular expressions must follow /app/docs/path-regexp-anchors.md: patterns compile as full-path anchored matches, not substring scans.

Header matchers must follow /app/docs/header-case-contract.md: when case_sensitive is unset or false, fold both header names and header values before comparison.

Terminal routes must follow /app/docs/handle-termination.md: when a matching route has terminal true, evaluation stops for that route group and must not fall through to handle_path siblings.

route export reads staging and last-match only (never re-parse raw route JSON). It writes the handler report to /app/output/route-handler.json and exports the handler @id from staging, not the route array index. Export must increment and echo the replay_seq from /app/state/caddy-commit.json per ingest cycle rules in the staging schema.

Bundled fixtures use the /app/data/routes directory. Hidden verifier fixtures may supply additional route directories at runtime.
