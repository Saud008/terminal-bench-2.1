# PipelineRun YAML subset

The planner accepts a single `PipelineRun` document with embedded `pipelineSpec`.

## Required shape

```yaml
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  name: <run-name>
spec:
  pipelineSpec:
    workspaces:
      - name: shared-data
        optional: false
      - name: credentials
        optional: true
    tasks:
      - name: <task>
        runAfter: [<task-names>]
        workspaces:
          - name: <task-ws>
            workspace: <pipeline-ws>
        taskSpec:
          workspaces:
            - name: <task-ws>
              mountPath: /workspaces/<task-ws>
              subPath: <optional>
          steps:
            - name: <step>
              runAfter: [<step-names>]
  workspaces:
    - name: <pipeline-ws>
      persistentVolumeClaim:
        claimName: <claim>
    - name: <pipeline-ws>
      emptyDir:
        medium: ""
```

## Field notes

- `taskSpec.workspaces` defines mount paths shared by all steps unless overridden per step.
- `subPath` when set creates a nested mount; parent path must be planned first.
- `runAfter` lists must be acyclic; cycles are errors.
