# Verifier trust math

Bundled pytest recomputes trust reports from fixture bundles using hashlib digests,
struct packing for authData fields, and uuid parsing for AAGUID values. The helper module
attest_verifier_math.py under tests/ and /app/scripts/trust_verifier_primitives.py document those primitives.
