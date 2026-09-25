# Canonical URL rules

Canonical URLs drive scope checks, duplicate resolution, and integrity digests.

1. Lowercase scheme and host.
2. Remove default ports (:80 for http, :443 for https).
3. Decode percent-encoding in the path for unreserved characters (ALPHA / DIGIT / - . _ ~).
4. Preserve `%2F` as encoded slash segments; do not decode reserved `%2F` into path separators during normalization.
5. Empty path becomes `/`.
6. Sort query parameters by key ascending; preserve URL-encoded query keys and values.
7. Do not add trailing slash except when the scope prefix itself ends with `/`.
