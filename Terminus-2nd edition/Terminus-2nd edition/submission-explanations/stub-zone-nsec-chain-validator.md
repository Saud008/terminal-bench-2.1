# Submission explanations — stub-zone-nsec-chain-validator

**Task folder:** tasks/stub-zone-nsec-chain-validator/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task builds the nsecval CLI that validates stub-zone DNSSEC denial chains from captured resolver JSON. It is hard because behavior is split across nsec-ordering.md, nsec3-params.md, wildcard-proof-order.md, stub-cache.md, and denial-chain.md. Fixing one module often passes bundled fixtures while hidden captures still fail. Agents must rebuild Go after edits, honor canonical DNS name ordering, and respect cache serial rules. Partial fixes show up quickly across about twenty behavioral tests.

## Solution Explanation

The oracle copies golden Go sources into internal/nsec, internal/nsec3, internal/stub, and internal/proof, then rebuilds nsecval. Chain validation uses canonical NSEC ordering without wildcard owners. The walker checks NSEC gaps before wildcards, verifies NSEC3 iteration params, and keys the denial cache by qname plus qtype with serial regression flush. Key insight is to follow doc contracts for ordering, hashing, and cache semantics instead of patching one obvious file.

## Verification Explanation

test.sh rebuilds nsecval before pytest runs. Tests call the CLI via subprocess and compare reports to an independent reference_nsec module so answers cannot be pasted. Cases cover bundled and hidden captures under verifier-fixtures, staging snapshot sha256, cache qtype isolation, and alternate capture directory probes. NOP on the starter image should score zero. After the oracle patches and rebuild, the full suite passes.
