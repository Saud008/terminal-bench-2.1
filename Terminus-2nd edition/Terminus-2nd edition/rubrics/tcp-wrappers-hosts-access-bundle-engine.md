# Platform rubric — tcp-wrappers-hosts-access-bundle-engine

**Task folder:** tasks/tcp-wrappers-hosts-access-bundle-engine/

Agent merges allow rules before deny with stable sequential indices per merge-contract.md, +3
Agent writes staging artifact with side-order-sensitive publish seal per publish-staging.md, +3
Agent computes fragment-sensitive bundle fingerprint before manifest bytes per session-cache.md, +3
Agent validates publish seal before writing merge cache entries, +3
Agent evaluates allow rules before deny including ALL deny rows per decide-contract.md, +3
Agent refreshes stale cache when fingerprint or publish seal diverges, +3
Agent handles multi-host ALL EXCEPT exclusions per cidr-matching.md, +3
Agent propagates replay checker exit status after writing export JSON, +3
Agent exports canonical daemon spellings without merge-cache fields in decide exports, +2
Agent matches IPv6 CIDR and daemon alias normalization per docs, +2
Agent leaves /app/docs and bundled fixtures unchanged, +2
Agent hashes manifest.json before fragment bytes in fingerprint, -3
Agent skips publish seal validation and trusts tampered cache, -3
Agent evaluates deny rules before allow rules in decide, -3
Agent returns replay exit zero after writing export despite mismatches, -3
Agent treats ALL EXCEPT as excluding only the first listed host, -2
