# Certificate chain linkage

cert_chain arrays list links from leaf to root. For adjacent pairs,
links[i].issuer_fp must equal links[i+1].subject_fp.

Root role entries must have subject_fp equal to issuer_fp.

When linkage validation fails, the trust decision trust_level must be rejected
with reason chain_invalid.
