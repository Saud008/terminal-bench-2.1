# Staging snapshot schema

Written by ingest to --staging path.

{
  "input_path": string,
  "input_sha256": string hex,
  "payload_len": integer,
  "outer_alg": integer,
  "outer_kid": string or null,
  "countersign_count": integer,
  "protected_key_order": [ integer, ... ] — label order used when canonicalizing outer protected map
}

protected_key_order must reflect canonical CBOR key byte order of labels present in outer protected headers.
