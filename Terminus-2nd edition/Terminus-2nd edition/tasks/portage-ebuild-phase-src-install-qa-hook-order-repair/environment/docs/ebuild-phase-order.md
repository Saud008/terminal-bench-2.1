# Ebuild src_install phase order

The mock phase driver under /app/lib/ebuild-phase implements src_install for sample package trees that ship a manifest.json file. Each package tree lives under /app/fixtures/ for public samples. Verifiers may point the driver at other absolute package tree paths when TB3_PACKAGE_ROOT is set.

## Required src_install step order

After doins materializes files under the destination root (the D variable, passed to the driver as --d), src_install must execute helper steps in this exact order. The driver appends each step name to /app/state/phase-trace.json in execution order.

1. doins — install files and symlinks from manifest entries into D
2. normalize_d — normalize directory permissions under D to 0755 and regular files to 0644 before any QA hook reads the tree
3. qa_preflight — run QA checks defined in /app/docs/qa-checks.md
4. fperms — apply explicit permission lines from the manifest fperms list
5. dosbin — strip setuid/setgid from paths listed in dosbin_paths without clearing fperms that were already applied
6. qa_postflight — repeat the same QA checks as preflight

QA hooks must never run before normalize_d completes. Postflight QA runs after fperms and dosbin.

## Setuid and dosbin interaction

When a manifest lists a path in both fperms with a setuid mode (leading digit 4) and in dosbin_paths, dosbin must not remove the setuid bit that fperms applied. Apply fperms before dosbin.

## Symlink containment

All symbolic links under D must resolve to a path contained in D. Symlink targets must be relative to the link directory or otherwise resolve inside D. Absolute targets pointing outside D are rejected by QA.

## CLI

Run from /app:

/app/bin/ebuild-phase run --tree PACKAGE_TREE --d DEST --phase src_install

Use /app/scripts/reset-state.sh before repeated runs when tests require a clean /app/state.
