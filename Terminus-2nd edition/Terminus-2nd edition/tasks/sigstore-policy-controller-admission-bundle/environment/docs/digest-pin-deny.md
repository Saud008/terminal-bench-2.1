# Digest pin deny

Digest-deny pins are exact normalized digests. If the pull image digest (substring after the final `@`, then normalized) equals any merged pin, the decision is terminal deny with reason digest_deny. Pins cannot be overridden by quorum, builder allow, or exceptions.

Merged cip-tiers union all deny digests. Normalization strips an optional sha256: prefix and lowercases hex.
