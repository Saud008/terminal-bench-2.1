# Dry-run deletion reclaim-sequence

emit-plan emits actions in safe order: deletable snapshots deepest first, then deletable images sorted by digest ascending.

Children must appear before their parent snapshot keys in the action list.
