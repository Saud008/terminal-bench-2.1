# Terraform plan semantics

This task uses a Terraform show -json subset. Each element of resource_changes is evaluated when change.actions is not exactly ["no-op"].

## Fields used

| Field | Meaning |
|-------|---------|
| address | Current resource address |
| previous_address | Present when actions include move |
| module_address | Parent module path or empty string |
| provider_key | Short provider binding key (for example aws, aws.east) |
| change.actions | Action list such as create, update, delete, move |
| change.before.tags | Tag map before change or null |
| change.after.tags | Tag map after change or null |

## Move actions

When move appears in change.actions, the resource is relocated. Effective before tags for policy comparison come from the resource_changes entry whose address equals previous_address when that entry exists in the same plan. If no previous entry exists, use change.before.tags merged with module defaults only.

Moved resources still participate in deny rules for their provider scope and actions.

## Computed unknowns

A tag value equal to the literal string (known after apply) means the after value is unknown. Record the canonical tag key in unknown_keys_after on the staging resource. Unknown keys must not generate MISSING_REQUIRED_TAG or TAG_DRIFT_REMOVE violations.

## Provider keys

provider_key is matched against provider_aliases in the policy file to obtain provider_scope for deny rule selection.
