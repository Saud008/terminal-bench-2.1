# CLI reference

Binary: `/usr/local/bin/tekton-mount-plan` (rebuild with `/app/scripts/verifier-rebuild.sh`).

## Commands

```bash
tekton-mount-plan parse --file /app/fixtures/<name>.yaml
tekton-mount-plan bind --file /app/fixtures/<name>.yaml
tekton-mount-plan plan --file /app/fixtures/<name>.yaml
```

All commands emit indented JSON on stdout. Non-zero exit on parse/bind/plan errors.

## Stages

| Stage | Module | Output type |
|-------|--------|-------------|
| `parse` | `/app/internal/parse/parse.go` | `ParsedPipeline` with `task_order`, declarations, bindings |
| `bind` | `/app/internal/bind/bind.go` | `BoundPipeline` with per-task resolved sources |
| `plan` | `/app/internal/plan/plan.go` | `MountPlan` mount sequence |

Repair only the module named in the milestone instruction. Do not edit `/app/docs/` or `/app/fixtures/`.
