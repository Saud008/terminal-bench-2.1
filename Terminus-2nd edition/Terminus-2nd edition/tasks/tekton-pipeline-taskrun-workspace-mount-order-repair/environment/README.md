# tekton-mount-plan

Offline Tekton PipelineRun workspace mount planner used for CI regression fixtures.

## Layout

- `/app/cmd/tekton-mount-plan` — CLI entrypoint
- `/app/internal/parse` — PipelineRun normalization and task DAG order
- `/app/internal/bind` — Pipeline/workspace binding resolution
- `/app/internal/plan` — Step mount sequence planner
- `/app/docs/` — Workspace semantics and JSON contracts
- `/app/fixtures/` — Public PipelineRun YAML samples (not golden mount lists)

## Quick start

```bash
/app/scripts/verifier-rebuild.sh
tekton-mount-plan plan --file /app/fixtures/dag-order.yaml
```

Read `/app/docs/workspace-semantics.md` before changing binding or mount ordering logic.
