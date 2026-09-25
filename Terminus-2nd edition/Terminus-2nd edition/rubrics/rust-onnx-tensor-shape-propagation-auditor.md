# Platform rubric — rust-onnx-tensor-shape-propagation-auditor

**Task folder:** tasks/rust-onnx-tensor-shape-propagation-auditor/

Agent propagates transitive dynamic dimension symbols across linked graph inputs, +3
Agent applies default_shape substitution for -1 input placeholders before propagation, +3
Agent implements numpy-style right-aligned broadcast for Add and Mul nodes, +2
Agent binds initializer tensors in graph declaration order without alphabetical resort, +3
Agent computes batched MatMul output ranks with leading batch broadcast, +3
Agent resolves Reshape -1 target dimensions using total element count over known axes, +2
Agent persists tensor_prop_batch.jsonl rows in ascending ordinal order per graph, +2
Agent emits constraint_diagnostic_report.json violations sorted by node_id code tensor, +3
Agent keeps totals.violation_count equal to violations array length, +2
Agent rebuilds shapeprop via build_all.sh before subprocess CLI grading runs, +1
Agent hardcodes ledger or report JSON instead of running shapeprop CLI, -5
Agent edits pytest or reference modules instead of Rust propagation code, -5
Agent leaves broadcast padding on the trailing axis instead of right alignment, -3
Agent skips TB3_GRAPH_DIR hidden graph batch override behavior, -3
