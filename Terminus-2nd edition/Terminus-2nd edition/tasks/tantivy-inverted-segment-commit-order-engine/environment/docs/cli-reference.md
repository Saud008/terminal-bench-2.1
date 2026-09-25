# CLI reference — tantool index-ops control plane

Operator verbs:

- ingest --index NAME --input PATH — admit one staging segment from JSONL add/delete ops
- merge --index NAME — merge all staging segments (requires at least two)
- commit --index NAME — WAL barrier and snapshot
- search --index NAME --field title|body --term TERM --out PATH — sealed JSON hit array from committed segments
- stats --index NAME — JSON stats on stdout

Environment TB3_INDEX_PREFIX when set to an absolute path builds index names as {prefix}/{index}.
