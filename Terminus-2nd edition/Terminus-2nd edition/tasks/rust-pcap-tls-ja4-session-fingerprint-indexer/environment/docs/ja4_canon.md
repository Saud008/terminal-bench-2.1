# JA4-style fingerprint normalization

The indexer emits a lowercase JA4-style string per session:

```
t<tls_version_hex>d<cipher_count_hex>h<extension_hash_12>_<alpn_prefix>
```

Rules:

1. `tls_version_hex` is two lowercase hex digits taken from the legacy ClientHello version field at bytes 4-5 of the ClientHello body (big-endian uint16). Use only this legacy field; do not read the supported_versions extension (type 0x002b) for this value. When the body is shorter than six bytes, treat the version as `0x0303`.
2. `cipher_count_hex` is two lowercase hex digits of the count of cipher suites offered, capped at 255.
3. Cipher suites are sorted ascending before counting.
4. Extensions are sorted ascending by type code before hashing.
5. `extension_hash_12` is the first 12 characters of the lowercase hex SHA-256 digest over sorted extension type codes encoded as big-endian uint16.
6. `alpn_prefix` is the first two characters of the first ALPN protocol name, or `00` when ALPN is absent.

ALPN wire layout inside the ClientHello extensions block:

- Locate extension type `0x0010` (application_layer_protocol_negotiation).
- Let `data` be the extension value bytes after the standard four-byte extension header.
- **Normalization:** bundled capsules omit the on-wire uint16 ExtensionList total-length prefix. The value begins at the first ProtocolName entry.
- Read `name_length = data[0]` as a single-byte length. When `len(data) >= 1 + name_length`, the first protocol name is the ASCII bytes at `data[1:1+name_length]`. Bundled fixtures encode ALPN as `\x02h2`, which yields the token `h2` and prefix `h2`.
- When the length check fails, treat ALPN as absent and use prefix `00`.

Emit reads staged `handshake_bytes` assembled during intake and locates the ClientHello body inside that byte stream before applying these rules.
