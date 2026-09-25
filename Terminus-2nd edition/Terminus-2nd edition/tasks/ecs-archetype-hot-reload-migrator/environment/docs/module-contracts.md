# ecs-core public API contract

Implementations under /app/crates/ecs-core/src/ must keep the public functions below available with unchanged signatures. After edits, run `cargo test -p ecs-core api_contract` to confirm the workspace still exposes the documented surface.

| Module | Function |
|--------|----------|
| migrator.rs | ordered_steps |
| migrator.rs | apply_steps |
| archetype.rs | rebuild_archetype_table(conn, manifest, chunks_dir) |
| entity_id.rs | remap_new_entity_ids(conn) -> Result<u32> |
| entity_id.rs | tombstone_ids(conn) -> Result<Vec<u32>> |
| journal.rs | load_journal |
| journal.rs | replay_start_cursor |
| journal.rs | mark_committed |
| checksum.rs | chunk_checksum |
| checksum.rs | decode_chunk |
