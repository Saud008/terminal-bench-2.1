# Partial stack withdraw data model

Vault stacks live in `item_stacks`. Withdrawn portions are tracked in `withdraw_slices`.

When withdraw quantity is less than the vault stack quantity, the remnant stays in `item_stacks` and the withdrawn quantity is recorded in `withdraw_slices` under a distinct `slice_id`. `item_template_id` and `guild_id` match on both sides.

Full-stack withdraw removes the vault row and records the entire quantity in `withdraw_slices`.

Across withdraws that do not transfer out, `SUM(item_stacks.quantity) + SUM(withdraw_slices.quantity)` for a guild is conserved. Transfer-out moves stacks to `player_stacks`.
