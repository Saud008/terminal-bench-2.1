# Submission explanations — hashicorp-hcl2-attr-block-composer

**Task folder:** tasks/hashicorp-hcl2-attr-block-composer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement hclctl ingest and merge export on a working Go baseline. Contracts in merge-contract.md, dynamic-blocks.md, export-checksum.md, and staging-schema.md split deep attribute merge, explicit null overrides, dynamic expansion order, label tie-breaks, and normalized JSON checksums across internal merge and export packages. A shallow merge or HCL text hash passes some bundled checks but fails nested tag traps and checksum tests. Hidden fixtures under /opt/verifier-fixtures add conflicting nested keys without dynamics so partial fixes still fail four TB3 tests.

## Solution Explanation

The oracle copies corrected internal merge and export pipeline sources into /app and rebuilds hclctl. Merge applies deep nested maps, honors null merge_override deletes, runs overrides before dynamic expansion, and picks export labels from the lowest source-order fragment. Export writes merged.hcl for review and derives merge-checksum.txt from recursively sorted normalized JSON. The decoy wrap module stays off the hot path.

## Verification Explanation

test.sh runs go build then twenty-four pytest cases via subprocess CLI calls to /app/bin/hclctl. reference_merge.py independently recomputes merged attributes and checksum digests from staging JSON so agents cannot paste golden files. Bundled fixtures cover staging order, null removal, label order, dynamics after overrides, and checksum versus HCL hash. Four hidden tests copy TB3 fixtures for deep merge poison and checksum traps. NOP fails four bundled tests on the starter tree. Oracle passes all twenty-four.
