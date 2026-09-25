# portfolio load schema

load-portfolio is the only verb that reads --scenario (and optional --fixture-dir). It loads grants, project_aliases, amendments, and expenses arrays from the scenario JSON into /app/state/grant-portfolio.db. Grants persist restriction_path, allowed_categories_json, ceiling_cents, and project linkage. Expenses persist category_path for overlap tests. Meta row scenario_id must match the CLI flag so later verbs can reuse that stored portfolio without re-passing --scenario.
