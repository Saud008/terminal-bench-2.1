The stage2-audit driver at /app/bin/stage2-audit simulates debootstrap second-stage bind mounts, chroot hooks, resolver seeding, and apt source lines for offline rootfs fixtures under /app/fixtures/rootfs/. Bundled layouts are listed in /app/docs/fixture-catalog.md.

Implement the /app/lib/ pipeline modules so stage2-audit run --rootfs <dir> --output <file> produces canonical mount DAG ordering, gate digests, staging manifests, and export reports for every catalog rootfs. Each pipeline stage must satisfy its contract in /app/docs/mount-dag.md, /app/docs/commit-gate.md, /app/docs/chroot-hooks.md, /app/docs/resolv-layout.md, /app/docs/apt-sources.md, /app/docs/staging-contract.md, and /app/docs/export-manifest.md. Intermediate artifacts use schema key version while the final audit report uses pipeline_version.

Do not modify /app/docs/, /app/fixtures/, or files under /tests/. The environment has no outbound network access.
