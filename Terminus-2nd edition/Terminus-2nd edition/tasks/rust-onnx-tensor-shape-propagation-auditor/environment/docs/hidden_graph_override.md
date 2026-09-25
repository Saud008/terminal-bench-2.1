# Hidden graph override

Grading may point TB3_GRAPH_DIR at an alternate graph batch directory that is not part of the bundled fixtures under /app/environment/fixtures/graphs. When the override is active, batch-propagate and emit-violations must read that directory instead of the bundled batch while preserving the same JSON report shape, ledger row ordering, and violation sort rules documented in diagnostic_contract.md.
