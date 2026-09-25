# Override precedence

Among overrides active for plan_id and ndc on as_of, select the highest priority integer.

Match override ndc to the drug's raw fixture ndc with exact string equality. Do not normalize either side when selecting the winning override.

When priority ties, defer to date-window-contract.md for effective_start tie-break.
