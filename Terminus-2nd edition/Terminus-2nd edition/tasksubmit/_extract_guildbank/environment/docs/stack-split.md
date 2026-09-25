# Partial stack withdraw split

Vault stacks live in item_stacks. Withdrawn portions are tracked in withdraw_slices.

Partial withdraw (quantity less than the vault stack quantity) must leave the remainder in item_stacks and record the withdrawn quantity in withdraw_slices with a distinct slice_id. item_template_id and guild_id must match on both sides.

Full-stack withdraw removes the vault row and records the entire quantity in withdraw_slices.

Conservation: SUM(item_stacks.quantity) + SUM(withdraw_slices.quantity) for a guild must remain constant across partial withdraws except for transfer-out, which moves stacks to player_stacks.
