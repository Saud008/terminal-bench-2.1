# scenario catalog

Bundled scenarios live under /app/fixtures/scenarios/. catalog.json lists the bundled scenario names used for replay checks.

Scenario 005-mail-fail-order uses batch ops and job fail (job key ops:fail) with exit_code 7 to exercise failure mail ordering after registry_delete.
