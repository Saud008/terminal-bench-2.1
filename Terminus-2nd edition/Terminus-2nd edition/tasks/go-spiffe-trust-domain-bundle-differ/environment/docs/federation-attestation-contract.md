# Federation trust attestation — SPIFFE mesh bundle reconciliation

## Core concept

Cross-cluster SPIFFE security operators attest two trust-domain bundle captures before admitting federation policy to downstream meshes. The control plane performs workload-identity trust attestation: SPIFFE URI host authenticity folding, JWKS signing-key precedence, x509 SVID serial integrity, federation wildcard allowlist admission, and dual temporal axes. Rotation ticks bound active signing material while observation ticks evict stale workload identities. This is not a generic application-engineering exercise, spectrophotometer ICC drift analysis, or rendering-intent precedence over LAB readings.

## Distinct trust gates

Trust-domain host folding strips spiffe scheme prefixes and lowercases DNS labels without reprecedence path segments. JWKS key precedence places all sig keys before enc keys with kid lex order within each use class. Rotation window inclusivity keeps SVIDs whose rotation tick falls within W ticks of the bundle tick per rotation-window-contract. Federation allowlist retains host-only wildcard patterns that match the normalized trust domain host. Stale SVID eviction drops identities whose observation tick lags the bundle tick by more than the stale threshold. Trust attest seal counter increments once per normalize-trust side write and emit-atlas requires a positive seal before writing federation-atlas.json. Federation atlas sorts identity deltas by JSON pointer path ascending and seals a stable report digest over change_count, changes, and scenario.

## Artifact contract

`bind-pair` stages pair-capture digests; `normalize-trust` materializes normalized trust sides and increments the trust-attest seal; `emit-atlas` refuses sealed export when the seal counter is zero. Hidden fixture roots and rotation-window overrides are tool inputs when those environment variables are present.
