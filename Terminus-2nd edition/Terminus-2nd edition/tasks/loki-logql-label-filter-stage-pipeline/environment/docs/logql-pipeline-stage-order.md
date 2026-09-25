# LogQL pipeline stage order

Offline lokictl eval runs query stages in file order left to right.

The label matcher stage must run on stream labels only before any json stage parses the log line body. Json parsing must not copy parsed fields into the label set before the matcher runs.

Stage file path: /app/state/logql-stage.json

Eval command: lokictl eval --query QUERY_FILE --lines LINES_JSONL
