`tekton-mount-plan plan` builds the final workspace mount sequence, but plan output does not satisfy `/app/docs/mount-plan-format.md` (including task order, step order, subpath ordering, and skipped-workspace handling). Milestone 3 covers **mount planning only** (earlier parse and bind behavior is assumed already correct).

Repair `/app/internal/plan/plan.go`. Do not edit `/app/docs/` or `/app/fixtures/`.

Rebuild and verify:

```bash
/app/scripts/verifier-rebuild.sh
tekton-mount-plan plan --file /app/fixtures/subpath-steps.yaml
```
