# Canonical JSON for signed metadata

Signed metadata bytes are the UTF-8 encoding of the canonical JSON representation of the signed object only (never the signatures array).

Rules:

1. Object keys are sorted lexicographically at every nesting depth.
2. No insignificant whitespace appears outside JSON string values.
3. Arrays preserve element order from the signed object.
4. Numbers render as JSON numbers without leading zero padding.
5. The canonical form is computed recursively; serde pretty printing or map iteration order must not be used for verification input.

All HMAC-SHA256 signatures in this workspace use the canonical bytes as the message.
