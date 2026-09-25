# Canonical URL rules

Canonical URLs drive scope checks, duplicate resolution, and integrity digests.

1. Lowercase scheme, host, and the full path-and-query string (after host extraction).
2. Remove default ports (:80 for http, :443 for https).
3. Apply percent-decoding to the entire path-and-query string first (this decodes `%2F` into `/` along with other escapes).
4. Split the path into segments and decode unreserved percent-escapes per segment (ALPHA / DIGIT / - . _ ~). Segments that still contain a literal `%2F` or `%2f` after step 3 (for example double-encoded slashes) are left unchanged.
5. Empty path becomes `/`.
6. Sort query parameters by key ascending; preserve URL-encoded query keys and values.
7. Do not add trailing slash except when the scope prefix itself ends with `/`.
