# Tag policy

Policy file schema version: policy_version (integer).

## Tag key map

tag_key_map maps canonical keys (for example cost_center) to display names used in Terraform tags (for example CostCenter). All staging and report fields use canonical keys.

## Provider aliases

provider_aliases maps provider_key values to provider_scope strings used by deny_rules.

## Module defaults

module_defaults is an ordered list of objects with module_prefix and tags. For a resource address, apply every entry whose module_prefix is a dot-boundary prefix of the address, shortest prefix first, merging tags so later entries override earlier keys.

Example: module.network.aws_vpc.main matches module.network.

## Deny rules

Each deny rule has:
- id: stable string identifier
- provider_scope: matches resolved scope after alias mapping
- require_keys: list of canonical keys that must appear in effective_tags_after
- on_actions: deny evaluation runs only when at least one action intersects this list

## Waivers

Each waiver has:
- id: stable string identifier
- match.resource: exact address match (highest precedence)
- match.module_prefix: prefix match (lower precedence than resource)
- keys: canonical keys waived from deny requirements
- expires: ISO date YYYY-MM-DD; waiver is invalid when policy evaluated_on is strictly after expires

## Precedence

1. Unknown after keys: exempt from deny and drift-remove for that key.
2. Resource-specific waiver beats module_prefix waiver for the same key.
3. Valid waiver suppresses MISSING_REQUIRED_TAG for listed keys only.
4. Deny rules apply when not waived.
5. TAG_DRIFT_REMOVE applies on update when a tag was present in effective_tags_before, absent in effective_tags_after, and not unknown after.

evaluated_on in the policy file is the waiver expiry reference date.
