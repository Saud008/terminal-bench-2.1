Implement the GNU Libtool dependency canonicalizer pipeline under /app/lib/ so /app/bin/lt-canonicalize can scan .la archives, stage ingest metadata, and export /app/output/libtool-manifest.json for downstream linking. The demo tree at /app/projects/demo is the reference project; your work completes scan ingest staging and manifest export behavior per /app/docs/la-format.md, /app/docs/manifest-schema.md, /app/docs/scan-snapshot.md, /app/docs/link-order.md, /app/docs/snapshot-validate.md, and /app/docs/fixture-catalog.md.

The scan ingest stage must walk in-project .la files, break cyclic dependency_libs edges deterministically, and write /app/state/lt-scan-snapshot.json including snapshot_fingerprint. The export publish stage validates that snapshot then reads it only (see /app/docs/scan-snapshot.md and /app/docs/snapshot-validate.md). Publish computes dependency_order through linkorder.sh, not the legacy topo.sh preview helper or decoy_topo.sh.

After your implementation, /app/bin/lt-canonicalize /app/projects/demo --out /app/output/libtool-manifest.json must succeed. Follow dependency_order rules in /app/docs/la-format.md (direct in-project dependencies only, with topological tie-breaking as documented there). The manifest must be sufficient to link /app/projects/demo/src/probe.c against the demo shared libraries with the expected runtime shared-library dependencies.

Dependency ids in dependency_order use the lib prefix form (libcore, libmath), not bare short names.

Do not edit /app/docs/, files under /app/projects/demo/.libs/, or files under /tests.
