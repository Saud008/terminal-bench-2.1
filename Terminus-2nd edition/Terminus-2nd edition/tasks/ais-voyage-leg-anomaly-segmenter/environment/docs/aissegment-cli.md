# CLI

Binary name aissegment with subcommands feed and atlas.

Feed flags: --input path or basename, --snapshot default /app/state/track-snapshot.json, --ports default /app/fixtures/ports.geojson (read for validation only during feed).
An absolute missing input path such as /app/fixtures/streams/does-not-exist.jsonl exits 1.

Atlas flags: --output default /app/output/voyage-atlas.json, --snapshot, --ports.

When TB3_AIS_DIR is an absolute directory, feed resolves --input to TB3_AIS_DIR joined with the basename of --input only.

Exit codes: intake missing input file 1, parse or IO success 0, parse failure 2. Atlas missing snapshot 1, empty points 2, success 0.
