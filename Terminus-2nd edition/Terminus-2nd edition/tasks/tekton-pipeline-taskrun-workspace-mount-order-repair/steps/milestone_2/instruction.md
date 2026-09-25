`tekton-mount-plan bind` resolves PipelineRun workspace volumes to tasks, but bind output does not match `/app/docs/workspace-semantics.md`. Milestone 2 covers **workspace binding only** (milestone 1 parse behavior is assumed already correct).

Repair `/app/internal/bind/bind.go`. Do not edit `/app/docs/` or `/app/fixtures/`.

Rebuild after patching:

```bash
/app/scripts/verifier-rebuild.sh
tekton-mount-plan bind --file /app/fixtures/binding-mix.yaml
```
