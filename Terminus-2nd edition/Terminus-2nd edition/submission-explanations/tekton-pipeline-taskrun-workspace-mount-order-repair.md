# Submission explanations — tekton-pipeline-taskrun-workspace-mount-order-repair

**Task folder:** tasks/tekton-pipeline-taskrun-workspace-mount-order-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because the agent must repair a three-stage Go CLI that plans Tekton PipelineRun workspace mounts, and each milestone isolates a different layer while later stages assume earlier ones are already correct. Contracts are split across /app/docs/workspace-semantics.md, /app/docs/pipelinerun-schema.md, and /app/docs/mount-plan-format.md, so fixing only alphabetical ordering in parse or only PVC kind mapping in bind still leaves plan output wrong. Milestone two requires resolving bindings by pipeline workspace name rather than task-local names, and milestone three adds step-level runAfter ordering plus parent-before-subPath mount sequencing that is inverted in the broken code. Optional workspaces must be skipped cleanly in bind and emit no mount rows in plan, which is easy to miss when agents patch one file and stop. Fourteen behavioral tests across three milestones, including injected task, claim, and step name mutations, require the full contract to line up rather than a single obvious edit.

## Solution Explanation

The oracle copies corrected Go sources into /app/internal/parse, /app/internal/bind, and /app/internal/plan across the three milestones, then rebuilds tekton-mount-plan with /app/scripts/verifier-rebuild.sh. Parse must emit task_order from a topological sort on runAfter instead of alphabetical sorting, while preserving optional flags on pipeline workspace declarations. Bind must look up volume sources by pipeline workspace name, mark unbound optional workspaces as skipped without inventing emptyDir stubs, and keep persistentVolumeClaim versus emptyDir kinds distinct. Plan must walk tasks in parse order, order steps by step runAfter, emit parent mounts before subPath mounts within each step, and omit mount entries for skipped optional workspaces. Each milestone oracle applies only the module under test so agents cannot pass later milestones with broken earlier stages left in place.

## Verification Explanation

Each milestone verifier rebuilds the Go binary in test.sh, then drives tekton-mount-plan parse, bind, or plan via subprocess with fresh fixture paths per test. An independent reference_planner module in the test tree recomputes expected JSON from the same YAML fixtures and docs cited in the milestone instructions, so hard-coded CLI output cannot pass. Milestone one verifies fixture integrity against a canonical SHA-256 manifest under /opt/verifier-fixtures and checks that injected task name suffixes still produce correct topological order. Milestones two and three mutate PVC claim names and step names at runtime using VERIFIER_SEED so solutions must follow the documented resolution rules rather than memorizing default bundle output. Full mount plan equality assertions on task order, step order, subPath ordering, and skipped-workspace absence catch partial fixes that satisfy only the bundled fixture names.
