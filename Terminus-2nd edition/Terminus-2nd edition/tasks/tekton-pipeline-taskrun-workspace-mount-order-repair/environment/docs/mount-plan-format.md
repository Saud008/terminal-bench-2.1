# Mount plan JSON format

`tekton-mount-plan plan --file <path>` writes a single JSON object to stdout.

## Top-level fields

| Field | Type | Meaning |
|-------|------|---------|
| `run_name` | string | `metadata.name` from the PipelineRun |
| `mounts` | array | Ordered mount entries across all tasks |

## Mount entry

| Field | Type | Meaning |
|-------|------|---------|
| `task` | string | Task name |
| `step` | string | Step name within the task |
| `workspace` | string | Task workspace name |
| `mount_path` | string | Container mount path |
| `sub_path` | string | Optional subPath segment |
| `kind` | string | Resolved volume kind (`persistentVolumeClaim` or `emptyDir`) |

Skipped optional workspaces produce **no** mount entries.

## Ordering contract

1. Tasks appear in topological `runAfter` order (same as `parse` `task_order`).
2. Steps within a task follow step-level `runAfter` topological order.
3. Within each step, parent mounts precede subpath mounts.
