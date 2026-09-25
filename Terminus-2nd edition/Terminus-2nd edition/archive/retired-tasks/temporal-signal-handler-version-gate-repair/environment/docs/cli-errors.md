# CLI errors

The temporal-signal-replay export subcommand uses these exit codes:

- **2** — scenario path does not exist on disk, unknown subcommand, or required flags omitted. A missing file is exit **2**, not **3**, even though the path cannot be read.
- **3** — scenario path exists on disk but JSON cannot be decoded or fails validation (for example an empty workflow_id). Use **3** only after the file is present; unreadable paths are **2**.

Successful export writes the report file and exits **0**.
