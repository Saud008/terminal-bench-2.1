# Overview

`wtstatus-export` converts Git worktree `status --porcelain=v2 -z` byte streams into JSON suitable for CI dashboards. Parsing splits on NUL record boundaries; classification applies rename/copy score thresholds and submodule gitlink detection before export.

See `/app/docs/contract.md` for repair obligations and `/app/docs/export-schema.md` for output shape.
