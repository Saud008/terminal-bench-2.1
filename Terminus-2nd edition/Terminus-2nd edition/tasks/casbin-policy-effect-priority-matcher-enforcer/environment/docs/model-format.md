# Model format

Models live under `/app/fixtures/models/` as `.conf` files.

Config `model` names the active schema (filename without `.conf`). The `.conf` documents the policy layout for operators; runtime admission follows `/app/docs/access-decision-contract.md` and `/app/docs/trust-admission-workflow.md` rather than dynamic model parsing.

Reference sections: `request_definition`, `policy_definition`, `role_definition`, `policy_effect`, `matchers`.
