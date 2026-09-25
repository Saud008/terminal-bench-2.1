The `tekton-mount-plan` CLI under `/usr/local/bin` loads Tekton PipelineRun YAML, but `parse` output does not match `/app/docs/workspace-semantics.md` and `/app/docs/pipelinerun-schema.md`. Milestone 1 covers **PipelineRun parsing only**.

Repair `/app/internal/parse/parse.go`. Do not edit `/app/docs/` or `/app/fixtures/`.

After patching:

```bash
/app/scripts/verifier-rebuild.sh
tekton-mount-plan parse --file /app/fixtures/dag-order.yaml
```
