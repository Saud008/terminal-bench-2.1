# Fixture catalog

Bundled scenarios under /app/fixtures/scenarios/:

| Name | Intent |
|------|--------|
| 001-single-spam | One spam release |
| 002-single-virus | One virus release |
| 003-duplicate-idempotent | Same request twice |
| 004-queue-id-trap | Queue-ID differs from Quarantine-ID |
| 005-mixed-batch | Spam and virus in one run |
| 006-missing-message | Release with no spool file |
| 007-partial-success | One success and one failure |
| 008-cross-queue-stress | Both queues populated |
| 009-chained-trap | Success, miss, duplicate, success |
| 010-meta-class-trap | Meta class disagrees with spool subdir |
| 011-hold-token-gate | Hold token policy scenario |
| 012-custody-class-trap | Multi-class custody scenario |

Each scenario provides requests.json and spool/ subtrees. Catalog metadata is in /app/fixtures/catalog.json.
