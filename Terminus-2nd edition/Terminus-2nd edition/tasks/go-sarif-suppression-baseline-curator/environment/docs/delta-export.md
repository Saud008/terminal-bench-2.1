# Delta export

emit writes /app/output/finding-delta.json after curate.

## Preconditions

- reconcile_revision on reconcile-revision.json must be greater than zero
- scan_revision on baseline-revision must equal scan_revision on finding-staging.json
- findings_digest on staging must match recomputation from staging findings per finding-staging.md

## Row categories

Each delta row uses exactly one category:

| Category | Meaning |
|----------|---------|
| new | Curated entry key absent from baseline |
| removed | Baseline row key absent from curated entries |
| drift | Curated entry with drift_from_baseline true |
| suppressed | Curated entry with suppressed true and not drift |
| unchanged | Curated entry matching baseline without drift or suppression |

Category precedence when multiple apply: drift beats suppressed beats unchanged. new and removed are mutually exclusive with other categories.

## delta_digest

Marshal finding-delta without delta_digest field using canonical sorted-key JSON (same algorithm as catalog digest in sibling tasks). Lowercase hex sha256 of UTF-8 bytes.
