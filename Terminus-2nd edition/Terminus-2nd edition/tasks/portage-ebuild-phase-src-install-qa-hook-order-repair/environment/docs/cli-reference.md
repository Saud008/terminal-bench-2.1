# ebuild-phase CLI reference

Binary: /app/bin/ebuild-phase

Subcommand run options:

- --tree PATH — directory containing manifest.json
- --d PATH — destination root (D) for installed files
- --phase NAME — src_install, src_test, or full

State files:

- /app/state/phase-trace.json — ordered step names for src_install
- /app/state/merge-ledger.json — merge records after full runs

Environment overrides:

- TB3_PACKAGE_ROOT — when set to an absolute directory, verifiers may resolve package names under that root instead of /app/fixtures

Reset: /app/scripts/reset-state.sh clears state and work directories.

Manifest schema fields used by the driver: name, eapi, entries, fperms, dosbin_paths, src_test.

Entry types: file (src, dest, mode), symlink (dest, target relative to package tree).
