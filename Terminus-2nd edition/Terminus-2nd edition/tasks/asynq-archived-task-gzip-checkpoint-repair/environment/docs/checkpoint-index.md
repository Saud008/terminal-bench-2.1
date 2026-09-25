# Checkpoint index

The index sidecar JSON schema version 1:

version — integer 1
members — array of member objects
tasks — array mapping task id to member_id and line index

Each member object:

member_id — integer starting at 0
file_offset — byte offset in bundle where gzip member begins
compressed_size — byte length of entire gzip member including header and footer
task_ids — ordered ids archived inside the member

Checkpoint rule: compressed_size and file_offset for a member must be recorded only after the gzip writer Close completes so the footer is present on disk.

Archive staging: before writing members, ingest writes /app/state/archive-snapshot.json with fields seed, scenario, ordered_ids (canonical dedupe order for pending tasks being archived).

Partial member rule: if a member write aborts mid-stream, do not append a member entry whose compressed_size spans incomplete bytes; the index must point only at readable gzip members.
