# Recipe version precedence

recipes.json contains a recipes array. Each recipe has recipe_name, version, effective_from_epoch, target_L, target_a, target_b.

For a batch with recipe_name R and created_at_epoch T, select the recipe where recipe_name equals R and effective_from_epoch is less than or equal to T with the maximum effective_from_epoch. If batch recipe_version_override is non-null, use that exact version when present instead of precedence walk.
