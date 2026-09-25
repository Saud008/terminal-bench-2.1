# Submission explanations — fontconfig-charset-alias-substitution-dag-governor

**Task folder:** tasks/fontconfig-charset-alias-substitution-dag-governor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task implements the fc-alias-check ingest and resolve governor on a Rust workspace that models fontconfig charset aliases, substitution preferences, and bitmap versus outline rejection rules. Agents must wire an ingest stage that writes /app/state/fc-compiled.json, a resolve stage that reads staging only, and a check command for alias cycles. Contracts are split across six docs and bugs span parse, dag, resolve, and staging modules plus a decoy helper that is not on the hot path. Partial fixes pass bundled catalog runs but fail hidden traps when only staging graph_hash or charset order is wrong, or when a four hop hidden config under extra verifier fixture directories is truncated.

## Solution Explanation

The oracle copies golden parse, dag, resolve, and staging modules from solution files, rebuilds fc-alias-check with offline cargo, and resets /app/state. Ingest merges optional inject fragments, records compile_seq and graph_hash, and preserves charset declaration order. Resolve loads staging, walks the alias DAG, applies substitution and rejection rules, and writes export JSON with compile_meta echoed from staging. The key insight is export must never re-read XML from config paths after ingest has already normalized the merged model.

## Verification Explanation

test.sh rebuilds fc-alias-check before pytest. Tests drive ingest and resolve through subprocess CLI calls and compare export JSON to an independent Python reference resolver. Partial broken module swaps from /opt/verifier-broken-fc prove parse, dag, resolve, and staging failures are independent. Hidden deep chain configs under /opt/verifier-fixtures/fc-configs require four hop alias expansion. Staging snapshot, compile_seq, and inject-sensitive graph_hash tests guard the two stage pipeline. Oracle installs all golden modules. NOP on the shipped baseline scores zero.
