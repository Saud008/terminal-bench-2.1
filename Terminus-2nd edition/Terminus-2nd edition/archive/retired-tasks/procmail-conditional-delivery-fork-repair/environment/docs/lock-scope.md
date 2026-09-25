# Lock scope

Lockfiles serialize recipe evaluation per message.

## Path layout

For a recipe with `lock=NAME` inside a block with scope id S (top-level scope is `root`; nested scopes append `/` and the parent recipe id), the lock path is:

`/app/state/locks/<scope_id>/<NAME>`

Only one recipe holding the same lock path may run at a time for a given message. If the lock is busy, the recipe is skipped and recorded in `skipped_recipes` with reason `lock_busy`.

## Nesting

Nested blocks inherit a new scope id: parent scope, `/`, parent recipe id. Inner `lock=` names must not collide with unrelated outer locks by sharing a flat global directory.

Locks persist across messages until `/app/scripts/reset-state.sh` clears `/app/state/locks/`.
