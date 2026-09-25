# Submission explanations — initramfs-hook-order-firmware-stager

**Task folder:** tasks/initramfs-hook-order-firmware-stager/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must complete a multi-stage Bash pipeline where hook prerequisite ordering, modalias gating, firmware inclusion, compression tagging, and reproducible manifest sorting all interact. Contracts live across staging-ledger, hook-prereq-order, modalias-firmware-map, compression-policy, and export-manifest docs, so fixing only topological sort or only manifest emission still fails bundled and hidden tests. The staging ledger must bind ingest rows before export seals a rootfs digest, which is easy to skip when hook scripts alone look correct. Hidden TB3 fixtures invert hook NN-prefix intuition, require glob suffix modalias matching, and disable hook rows via config while keeping module paths. Partial fixes in one library module typically pass a subset of catalog fixtures but fail cross-run manifest digest and hidden trap cases.

## Solution Explanation

The oracle replaces eight golden irfs_*.sh modules under /app/lib with corrected hook topo sort, modalias glob matching, firmware map filtering, compression suffix rules, JSONL ledger sealing, and LC_ALL=C manifest sorting. The CLI ingests each rootfs tree, discovers hooks, selects modules via modules.load plus modules.alias against pci.ids, resolves firmware.map paths, tags compression per extension, appends ledger rows, seals irfs-manifest.json, verifies the seal, then writes the tab-separated manifest. Key insight is that irfs_topo_sort_hooks must read piped JSON from stdin while the Python driver uses -c, and rootfs_sha256 must hash every file in sorted path order. Export-only patches without ingest ledger fixes fail manifest digest and entry_count assertions.

## Verification Explanation

Pytest runs twenty-eight behavioral cases after reset-state, driving /app/bin/irfs-stage via subprocess on catalog rootfs trees and synthetic seeded layouts. An independent reference_stager.py recomputes expected manifest bytes, hook order, and seal JSON so hard-coded outputs cannot pass. Tests assert explicit paths /app/state/irfs-ledger.jsonl and /app/state/irfs-manifest.json plus /app/output/initramfs.manifest. Hidden fixtures under /opt/verifier-fixtures/initramfs exercise prereq inversion, suffix glob modalias, and include_hook_scripts false without appearing in the bundled catalog. Seeded VERIFIER_SEED inputs and ad-hoc PCI IDs block memorizing catalog manifest bytes.
