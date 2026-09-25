# SPIFFE mesh security context

Security operators compare trust-domain bundle pairs during federation cutovers. Each bundle snapshot carries trust_domain, bundle_epoch, JWKS keys, x509 SVID entries, federation allowlist patterns, and workload last_seen epochs. The attestation plane evaluates trust-policy consistency before admitting a new bundle to downstream meshes.
