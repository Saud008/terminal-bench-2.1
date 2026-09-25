# Diagnostic tags reference

Diagnostic tags are unsigned integers paired with labels. They are copied verbatim from ingest into staging and echoed in export attestation reports.

## Common tags

| Label | Tag | Notes |
|-------|-----|-------|
| self-describe-cbor | 55799 | RFC 7049 self-describe |
| encoded-cbor-item | 24 | Nested CBOR item marker |
| profile-alpha | 222315 | Bundled alpha fixture |
| profile-beta | 222316 | Bundled beta fixture |
