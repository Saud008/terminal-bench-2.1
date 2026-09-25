# Tekton workspace semantics (reduced model)

This tool implements a **subset** of Tekton PipelineRun workspace behavior for offline mount planning. Authoritative rules live here and in `/app/docs/pipelinerun-schema.md`.

## Pipeline-level workspaces

`spec.pipelineSpec.workspaces` declares names used across tasks. Each entry may set `optional: true`. When optional and no `spec.workspaces` binding exists for that name, the binder **skips** the workspace (no volume, `skipped: true` in bind output).

`spec.workspaces` on the PipelineRun supplies concrete volume sources:

| YAML key | `kind` in JSON output |
|----------|----------------------|
| `persistentVolumeClaim.claimName` | `persistentVolumeClaim` |
| `emptyDir.medium` | `emptyDir` |

Kinds must not be swapped or inferred from task-local names.

## Task workspace bindings

Each `pipelineSpec.tasks[].workspaces` entry maps a **task workspace name** (`name`) to a **pipeline workspace** (`workspace`). Binding resolution looks up the pipeline workspace name in `spec.workspaces`, not the task-local name.

Required pipeline workspaces without a PipelineRun binding make `bind` fail with a non-zero exit.

## Task ordering (parse stage)

`parse` emits `task_order` as a topological ordering of `pipelineSpec.tasks` using each task's `runAfter` list. **Alphabetical sorting is wrong** when it places a task before its dependencies.

## Step mount ordering (plan stage)

Within each task, steps are ordered topologically by `taskSpec.steps[].runAfter`.

For each step, workspace mounts are emitted in this order:

1. Mounts **without** `subPath` (parent/root mounts)
2. Mounts **with** `subPath` (nested paths)

Subpath mounts must never appear before their parent mount for the same workspace within a step.
