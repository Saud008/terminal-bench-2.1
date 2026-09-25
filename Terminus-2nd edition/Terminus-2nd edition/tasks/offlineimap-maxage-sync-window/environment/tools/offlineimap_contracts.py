FOLDER_SNAPSHOT_KEYS = frozenset({"schema", "account", "folders", "folder_digest"})
FOLDER_ENTRY_KEYS = frozenset({"name", "uidvalidity", "selected"})
SYNC_RUN_KEYS = frozenset(
    {"schema", "account", "reference_epoch", "synced_messages", "synced_bytes", "dry_run"}
)
