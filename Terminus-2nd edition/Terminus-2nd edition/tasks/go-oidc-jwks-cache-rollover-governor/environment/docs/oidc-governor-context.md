# OIDC JWKS cache rollover governor context

Offline reconstruct tool for identity platform CI. Validates JWT verification policy against recorded JWKS timelines without network fetches.

Tokens are synthetic records with kid, iss, aud, iat, exp, and signature_epoch aligned to timeline epochs.
