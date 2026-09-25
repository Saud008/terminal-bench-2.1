# Submission explanations — ansible-role-variable-precedence-reconciler

**Task folder:** tasks/ansible-role-variable-precedence-reconciler/
**Platform form only** — not in upload zip.

## Difficulty Explanation

The ansible-var-merge CLI at /app resolves effective variables for one inventory host across three milestones. Agents must follow variable-precedence.md, merge-behaviour.md, and fixture-catalog.md while repairing several bash modules under /app/lib/. The broken baseline merges inventory before role defaults, reverses role defaults and vars inside roles, applies include_vars lexically, and merges extra vars before playbook vars. Partial fixes pass some pytest cases but fail worker_pool collision checks, hash merge cache.enabled preservation, or independent reference_resolve comparisons. Milestone traps install golden inventory or role modules with broken precedence to prove one-file patches are insufficient.

## Solution Explanation

The oracle copies corrected inventory.sh, role.sh, merge.sh, include_vars.sh, and precedence.sh into /app/lib across milestone solve scripts. resolve_stack must apply role defaults, inventory group and host vars, role vars, include_vars sorted by depth, playbook vars, then extra vars. apply_var_layer must deep-merge nested dicts when hash_behaviour is merge. resolve_role_vars merges defaults before vars per role. Milestone two adds precedence ordering so inventory overrides nginx default worker_pool before role vars apply. Milestone three completes merge behaviour and extra-var precedence for the full m3-merge playbook with seeded host var injection tests.

## Verification Explanation

Each milestone test.sh resets /app state and runs pytest with reference_resolve.py as an independent Python reference that recomputes the documented layer stack from YAML fixtures. Tests invoke ansible-var-merge resolve via subprocess and compare JSON exports to the reference for multiple hosts and seeds. Milestone two asserts worker_pool collisions where inventory beats role defaults. Milestone three adds hash merge cache shape checks, include_vars depth ordering, extra vars beating playbook vars, and partial golden-lib traps. Oracle solve scripts patch all required lib modules before verifier runs.
