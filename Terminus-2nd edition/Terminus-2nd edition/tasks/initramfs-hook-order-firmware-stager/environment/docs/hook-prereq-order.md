# Hook prerequisite ordering

Initramfs hooks live under hooks/ inside the rootfs fixture. Each file is named NN-name.sh where NN is a decimal run weight used only for tie-breaking.

## Hook metadata lines

Each hook script may declare:

```
# PREREQ=hook_a,hook_b
# HOOK=custom_name
```

If HOOK is absent, the hook name is the basename with the NN- prefix and .sh suffix removed (40-firmware.sh becomes firmware).

PREREQ is a comma-separated list of hook names that must execute before this hook. Names are case-sensitive. An empty PREREQ means no prerequisites.

## Topological order

irfs-stage must compute a total order where every prerequisite appears before dependents. When multiple hooks are ready, pick the smallest NN prefix, then lexicographically smallest hook name.

Cycles are invalid: if a cycle is detected, exit status 2 and write no manifest.

## hook_rank column

The export manifest hook_rank field is the 1-based index of the hook in topological order. Module and firmware rows inherit the hook_rank of the modules or firmware hook that stages them (see export-manifest.md).
