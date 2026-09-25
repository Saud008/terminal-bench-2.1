# Operator graph and subtask mapping

operator_graph.json under fixtures/config defines operators array:

| Field | Type | Notes |
|-------|------|-------|
| operator_id | string | |
| parallelism | int | Subtask count |
| vertex_index | int | Topological order starting at 0 |

Global subtask_index in events refers to Flink logical subtask index within the operator_id on that event line, not a global job index.

Mapping uses operator_id on the event directly. Subtask indices must stay within [0, parallelism-1] for that operator. Cross-operator attribution is invalid.
