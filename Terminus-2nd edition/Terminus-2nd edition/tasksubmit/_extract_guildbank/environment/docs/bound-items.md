# Bound item transfer-out

`item_stacks.bound = 1` marks guild-bound gear that cannot leave the vault through transfer-out.

`POST /v1/guild/{guildId}/transfer-out` must return **409** when the target stack is bound.

Unbound stacks move to `player_stacks` and are removed from `item_stacks` atomically.

Bound stacks may still be withdrawn through `withdraw/stack` into `withdraw_slices` for authorized guild members.
