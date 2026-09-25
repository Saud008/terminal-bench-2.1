# Scope rules, duplicates, and integrity digests

## Scope prefix matching

A URL is in scope when its canonical form matches any scope prefix with **boundary rules**:

- If the scope ends with `/`, the URL must start with the scope string.
- If the scope does **not** end with `/`, the character immediately after the prefix in the URL must be `/` or the URL must end exactly at the prefix length.

Example: scope `https://cdn.example/app` matches `https://cdn.example/app/page` and `https://cdn.example/app/index` but not `https://cdn.example/applet`.

Independent verification may compare IHSH digests using the stdlib parity helpers in /app/environment/scripts/wble_stdlib_parity.py (struct little-endian reads, hashlib SHA-256, urllib percent-decoding).

## Duplicate exchanges

When multiple exchanges share the same canonical URL within one bundle, keep the row with the **highest variant_id** after canonicalization.

## Integrity digest preimage

SHA-256 over UTF-8 bytes concatenated as:

```
canonical_url + "\n" + decimal status + "\n" + normalized_headers + "\n" + raw body
```

Normalized headers: header names lowercased, values trimmed, sorted by name ascending, rendered as `name:value` lines joined by newline.

## Content-Type policy

Compare only the MIME base type before `;`. Parameters such as charset must be ignored when checking allowed_mimes.

## Ingest and export pipeline

```
wbleguard catalog-bundles --bundles-dir <DIR> --staging /app/state/exchange_attestation.jsonl
wbleguard emit-attestation --staging /app/state/exchange_attestation.jsonl --out /app/output/bundle_attestation_report.json
```

Staging lines sort by **canonical_url** ascending.

Export totals must count scope_violations separately and include them in finding_count.

When TB3_BUNDLE_DIR is set, catalog-bundles reads bundles from that directory instead of bundled fixtures.

Hidden grading bundles live under /opt/verifier-fixtures/wble_hidden/bundles when present in the runtime image.
