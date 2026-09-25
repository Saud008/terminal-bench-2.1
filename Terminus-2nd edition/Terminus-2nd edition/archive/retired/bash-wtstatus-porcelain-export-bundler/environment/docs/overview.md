# Overview

This task is a **build-and-dependency-management** host-local wtstatus-export status-export bundler. Operators admit offline Git `status --porcelain=v2 -z` fixture streams into the bundler, enforce rename/copy score gates and submodule gitlink detection during classification, then publish sealed JSON exports from classified entries only. The working baseline under `/app` must keep porcelain admission, score gates, and sealed export aligned; it is not a generic service repair exercise.

`wtstatus-export` converts worktree porcelain byte streams into JSON suitable for local build dashboards. Parsing splits on NUL record boundaries; classification applies rename/copy score thresholds and submodule gitlink detection before export.

See `/app/docs/contract.md` for admission and export obligations and `/app/docs/export-schema.md` for output shape.
