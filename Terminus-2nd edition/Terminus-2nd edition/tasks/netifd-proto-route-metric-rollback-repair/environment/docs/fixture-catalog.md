# Fixture catalog

Bundled scenarios live under /app/fixtures/scenarios/. Each file is one JSON object consumed by apply.

| Scenario | Exercises |
|----------|-----------|
| default-route | Kernel-assigned default route metric |
| hotplug-burst | Duplicate hotplug address dedup |
| pd-reload | PD lease release across reload |
| teardown-order | Teardown step ordering (run_teardown marks scenarios used with a separate teardown command) |
| rule-commit | Snapshot only after rules committed |

Hidden verifier scenarios may appear under TB3_FIXTURES_DIR when set to an absolute directory.

See /app/fixtures/catalog.json for names.
