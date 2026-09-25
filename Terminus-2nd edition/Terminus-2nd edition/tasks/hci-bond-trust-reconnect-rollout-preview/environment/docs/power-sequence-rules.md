# Power-sequence gate contract

Every adapter declares a `power_plan` of `cycle` or `off_first`.

- `power_plan: "cycle"` never blocks any device on this adapter through this gate, regardless of `disconnect_before_power`. A power cycle re-establishes the radio state on its own, so no explicit disconnect record is required.
- `power_plan: "off_first"` requires every device on that adapter to carry `disconnect_before_power: true`. A device on an `off_first` adapter with `disconnect_before_power` missing or `false` is blocked with reason `ineligible_power_sequence`.
- Any `power_plan` value other than `cycle` or `off_first` is not a supported plan; every device on that adapter is blocked with reason `ineligible_power_sequence`.

This is the only rule this gate enforces. It does not inspect any other device field.
