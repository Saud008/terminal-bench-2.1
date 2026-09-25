# Fixture catalog

Bundled stacks under /app/fixtures/rules:

- stack-alpha — numeric prefix ordering trap (2-wheel.rules vs 10-default.rules)
- stack-beta — secondary ordering sample
- stack-cache — implicit yes rules for cache scenarios

Hidden stacks ship under /opt/verifier-fixtures/rules/ and are selected when scenarios set rules_stack to hidden-js-win or hidden-seat-cache while TB3_RULES_DIR=/opt/verifier-fixtures.

See /app/fixtures/catalog.json for automated scenario names.
