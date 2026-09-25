# WBLE bundle wire format

Version 1 bundles begin with magic bytes WBLE followed by uint16 little-endian version 1.

## Header

1. Primary URL (uint16 LE length + UTF-8)
2. Scope prefix count (uint16 LE)
3. Scope prefixes (each uint16 LE length + UTF-8)
4. Allowed MIME count (uint16 LE)
5. Allowed MIME types (each uint16 LE length + UTF-8, base type only such as text/html)

## Exchanges

Exchange count is uint32 **little-endian**.

Each exchange:

- variant_id uint32 LE
- url uint16 LE length + UTF-8
- status uint16 LE
- header count uint16 LE
- headers: name/value pairs (each uint16 LE length + UTF-8)
- body length uint32 LE + raw body bytes

## Integrity section

After all exchanges, optional section IHSH:

- hash count uint32 LE
- each hash is 32 raw bytes SHA-256

Integrity hashes correspond to exchanges **in file order before duplicate resolution**, one hash per raw exchange row.

Bundled grading fixtures use bundle_id values alpha and bravo under /app/environment/fixtures/bundles.
