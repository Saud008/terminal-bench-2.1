# Fixture catalog

Bundled rootfs fixtures under /app/fixtures/rootfs/:

| Name | Notes |
|------|-------|
| rootfs-001 | standard bookworm layout |
| rootfs-002 | extra sysfs ordering stress |
| rootfs-003 | merged /usr layout |
| rootfs-004 | suite_retry=1 idempotent sources |
| rootfs-005 | hook expects dev marker |
| rootfs-006 | nested devpts bind ordering |
| rootfs-007 | trixie codename variant |
| rootfs-008 | hook failure must surface in ok |

Verifier-only hidden layouts ship under /tests/hidden_rootfs/ and are copied into /app/fixtures/rootfs/ at verify time.
