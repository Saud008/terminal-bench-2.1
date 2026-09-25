# Compressor metadata fingerprint

The compressor fingerprint is the first 16 hex characters of SHA-256 over UTF-8:

```
{id}:{level}:{shuffle}
```

All three fields are required in the payload even when zero.

Export uses the per-array fingerprint from staging; consolidated export does not re-hash compressor options from manifests.
