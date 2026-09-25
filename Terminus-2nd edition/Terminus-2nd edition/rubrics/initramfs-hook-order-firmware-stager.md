# Platform rubric — initramfs-hook-order-firmware-stager

**Task folder:** tasks/initramfs-hook-order-firmware-stager/

Agent topologically sorts hooks honoring PREREQ with NN-prefix then name tie-break, +3
Agent writes irfs-ledger.jsonl rows with monotonic seq and kind path hook_rank fields, +3
Agent seals irfs-manifest.json with rootfs tree digest and ledger_sha256 before export, +3
Agent matches modules.alias glob patterns against pci.ids for modules.load entries, +3
Agent includes firmware.map blobs only for modalias-selected modules under lib/firmware, +3
Agent applies compression policy with lowercased extension suffix for ko bin sh paths, +2
Agent emits manifest rows sorted by path using LC_ALL=C not size or legacy decoy sort, +2
Agent assigns module and firmware hook_rank from modules or firmware hook stage, +2
Agent honors include_hook_scripts false by omitting hook rows while keeping modules, +2
Agent ignores irfs_sort_legacy decoy ordering off the export hot path, +1
Agent patches only hook name sort while leaving PREREQ DAG unresolved, -3
Agent fixes firmware glob but keeps firmware.map rows for unselected modules, -3
Agent seals manifest with directory basename digest instead of sorted file walk, -2
Agent writes ledger as plain TSV instead of JSONL seq contract, -2
Agent matches modalias with prefix-only compare ignoring star suffix glob, -2
