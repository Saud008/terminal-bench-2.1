# Platform rubric — go-spiffe-trust-domain-bundle-differ

**Task folder:** tasks/go-spiffe-trust-domain-bundle-differ/

Agent canonicalizes trust domain hosts by stripping spiffe scheme and lowercasing DNS labels, +3
Agent orders JWKS keys with all sig keys before enc keys sorted by kid, +3
Agent normalizes x509 SVID serial strings by stripping leading zeros, +3
Agent applies inclusive rotation tick window using TB3_ROT_WINDOW override, +3
Agent filters federation allowlist with star-dot host wildcard matching, +3
Agent drops stale workload identities below bundle tick minus stale threshold, +3
Agent computes pair-capture staging digest over left right and scenario keys, +2
Agent increments trust attest seal counter on normalize-trust side writes, +2
Agent blocks emit-atlas until seal counter is positive, +2
Agent sorts federation atlas changes by JSON pointer path ascending, +2
Agent seals report digest over change_count changes and scenario, +2
Agent honors hidden TB3 fixture directory for federation wildcard trap, +2
Agent rebuilds spiffectl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent swaps left and right bundle sides during bind-pair capture, -3
Agent uses exclusive rotation window bounds instead of inclusive tick range, -3
Agent emits atlas before normalize-trust completes seal increment, -3
Agent sorts atlas changes in descending path order, -3
