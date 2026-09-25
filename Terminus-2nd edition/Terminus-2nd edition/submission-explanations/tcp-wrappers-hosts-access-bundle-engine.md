# Submission explanations — tcp-wrappers-hosts-access-bundle-engine

**Task folder:** tasks/tcp-wrappers-hosts-access-bundle-engine/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because hostsctl spans eight Bash modules that must agree on merge ordering, staging seals, fragment fingerprints, cache refresh, CIDR matching, daemon aliases, and replay exit semantics. Contracts are split across nine /app/docs files, so patching only merge.sh or only cidr.sh leaves decide and replay failing on independent reference checks. Partial-fix traps swap individual lib files back to broken variants and still expect divergent exports, which catches one-module repairs that pass the default bundle. Models often fix allow-before-deny ordering but miss publish-seal binding, ALL EXCEPT multi-host handling, or replay exit-code propagation after JSON export.

## Solution Explanation

The oracle restores corrected Bash libraries under /app/lib and relies on the preinstalled hostsctl wrapper without editing docs or fixtures. Merge must stage payloads, compute fragment-before-manifest fingerprints, and write publish seals that bind allow-then-deny order before caching merged rules. Decide reloads or refreshes stale cache rows when fingerprint or publish seal diverges, evaluates allow rules before deny including ALL rows, and exports canonical daemon names without cache metadata. Replay re-runs decide per session row, writes the export JSON, then returns the checker status so a non-zero exit survives the write path.

## Verification Explanation

Pytest rebuilds lib scripts via verifier-rebuild.sh, resets workspace state, and drives hostsctl merge, decide, and replay through subprocess on every run. An independent reference_decide module recomputes merge exports and decisions from the same bundle fixtures, so static JSON files cannot pass. Tests assert staging and merged cache artifacts, publish seals, fingerprint bytes, seed-derived dynamic bundles, and session replay mismatches. Partial-trap tests install broken_lib variants for common.sh, decide.sh, merge.sh, cidr.sh, and publish.sh to ensure bundled green paths do not mask missing cross-module behavior.
