# Submission explanations — libtool-la-dependency-canonicalizer

**Task folder:** tasks/libtool-la-dependency-canonicalizer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a two stage Libtool pipeline where scan ingest writes a fingerprinted snapshot and export publish reads that snapshot only. Behavior is spread across nine docs and nine bash modules under /app/lib. Cycle breaking, lib prefixed dependency ids, topological linkorder, and rpath dedupe interact so one file fixes pass bundled tests but fail hidden fixtures. Partial fixes to graph or linkorder alone still sort dependencies alphabetically. About twenty seven tests include hidden trees under /opt/verifier-fixtures that need different ordering and static library fields.

## Solution Explanation

The oracle installs corrected bash modules from golden scripts, rebuilds ltparse with make, rebuilds demo shared libraries, then runs lt-canonicalize on the demo tree. Scan ingest loads la files, breaks cycles, and stages lt-scan-snapshot.json. Export publish validates the fingerprint and builds libtool-manifest.json through linkorder.sh not the decoy topo preview helper. The key insight is publish must never re walk la files after staging.

## Verification Explanation

test.sh rebuilds demo libraries before pytest. Tests call /app/bin/lt-canonicalize through subprocess and compare output to an independent Python reference walker. Hidden cases use extra fixture roots under /opt/verifier-fixtures for cross dependency ordering and static only installed libraries. Snapshot tests prove publish survives corrupted la files on disk. Tampered fingerprint cases must fail publish. Partial golden inject tests confirm decoy and single module fixes stay insufficient.
