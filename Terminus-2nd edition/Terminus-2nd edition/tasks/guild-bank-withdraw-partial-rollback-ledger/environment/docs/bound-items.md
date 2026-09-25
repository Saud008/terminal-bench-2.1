# Bound item transfer-out

`item_stacks.bound = 1` marks guild-bound gear that cannot leave the vault through transfer-out. Bound transfer-out returns **409** and leaves the stack in `item_stacks`. Unbound stacks move to `player_stacks` and leave `item_stacks`. Bound stacks may still be withdrawn through `withdraw/stack` into `withdraw_slices`.
