# Name key canonicalization

Canonical cache keys combine domain and name:

- Lowercase the domain label only (ASCII)
- Preserve name case exactly as logged
- Join with a single NUL byte (0x00) between domain and name

Example: domain CORP.EXAMPLE and name Alice yields corp.example\x00Alice.

Keys must not fold name case and must not merge principals from different domains even when names match case-insensitively.

Environment override SSSD_DOMAIN_SUFFIX replaces config domain_suffix for ingest when set to a non-empty absolute domain string.
