# Snapshot validation contract

`pulumi-dep-export order` must call `validate.ValidateSnapshot` before graph construction. Validation failures return exit code 3 from the CLI.

## Required checks

| Check | Policy |
|-------|--------|
| Stack name | `stack` must be non-empty |
| Snapshot version | `version` must be **≥ 3** (versions 1 and 2 are rejected) |
| Resource list | At least one resource row |
| Dependency URNs | Every `dependencies` entry must name a resource URN present in the snapshot |
| Provider URNs | When `provider` is set, it must name a resource URN present in the snapshot |
| Parent URNs | When `parent` is set, it must name a resource URN present in the snapshot |

Validation runs on the parsed snapshot **before** `FlattenComponents` or `BuildAdjacency`. Graph build must not run when validation fails.
