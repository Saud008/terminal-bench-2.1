# Compression policy

Compression tags are logical labels for cpio packaging, not on-disk transforms.

Lookup uses the final path extension lowercased (for example .ko, .bin, .sh). The compression map in stage.json maps extension strings to tags none, gz, or xz. When an extension is absent, use the default entry.

Extension matching is case-insensitive on the suffix only; .KO and .ko both map to the .ko rule.

Hook scripts ending in .sh use the .sh rule even when staged from hooks/.
