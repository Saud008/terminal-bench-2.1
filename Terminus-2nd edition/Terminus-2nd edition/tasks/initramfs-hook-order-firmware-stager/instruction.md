Implement the irfs-stage CLI at /app/bin/irfs-stage to build reproducible initramfs cpio manifests from miniature rootfs fixture trees. The tool ingests initramfs hook scripts, kernel module selections, modalias maps, and firmware blobs through the staging ledger in /app/docs/staging-ledger.md, resolves hook prerequisite ordering per /app/docs/hook-prereq-order.md, matches firmware via modalias rules in /app/docs/modalias-firmware-map.md, applies compression tags from /app/docs/compression-policy.md, and exports a byte-stable manifest per /app/docs/export-manifest.md.

The scaffold under /app/lib/ (hooks, modalias, firmware, compress, ledger, manifest, scan) does not yet satisfy those contracts. The legacy helper /app/lib/decoy/irfs_sort_legacy.sh is not authoritative for manifest ordering.

/app/bin/irfs-stage --rootfs PATH --config /app/config/stage.json --output /app/output/initramfs.manifest

Staging writes /app/state/irfs-ledger.jsonl and seals /app/state/irfs-manifest.json before export emits /app/output/initramfs.manifest.

If --rootfs is missing or not a readable directory, exit with status 1.

Bundled fixture layouts are described in /app/docs/fixture-catalog.md. Do not edit /app/docs/, /app/fixtures/, /app/config/stage.json, or files under /tests/.
