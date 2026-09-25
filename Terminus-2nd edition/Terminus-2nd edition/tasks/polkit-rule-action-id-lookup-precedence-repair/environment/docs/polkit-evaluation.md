# Polkit evaluation contract

pkctl evaluate reads a scenario JSON file and returns a single decision object on stdout.

## Scenario schema

Required fields:

- action_id — string action identifier
- subject — object with user (string), local (boolean), active (boolean), seat (string)
- rules_stack — name of a directory under the active rules root containing .rules files
- challenge — null or one of auth_admin, auth_self, auth_admin_keep

Optional:

- prior_grant — null or object with challenge (auth_admin or auth_admin_keep) and seat matching subject.seat

The active rules root is /app/fixtures/rules unless TB3_RULES_DIR is set to an absolute path, in which case stacks are resolved as TB3_RULES_DIR/rules_stack.

## Decision schema

Stdout is JSON with:

- decision — allow, deny, challenge, or cached_allow
- source — rule:FILENAME, action:js:ID, action:xml:ID, cache, or none
- challenge — echoed challenge type when decision is challenge, else null
- implicit — true when the outcome is an implicit yes without interactive challenge
- matched_rule — filename of the winning rule block or null

Evaluation order:

1. Merge rule files for rules_stack (see /app/docs/rule-precedence.md).
2. Select the last matching block for action_id and subject constraints.
3. If no block matches, resolve action defaults (see /app/docs/action-registry.md).
4. Map allow_active / allow_inactive for local subjects (see /app/docs/subject-matching.md).
5. Apply challenge and prior_grant handling (see /app/docs/challenge-types.md).
6. Read or write implicit authorization cache (see /app/docs/auth-cache.md).

## Result tokens

Rule blocks and action defaults use these result tokens:

- yes — implicit allow
- no — deny
- auth_admin — require admin authentication
- auth_admin_keep — admin authentication that may be retained for the seat
- auth_self — require owner authentication

Challenge scenario values interact with prior_grant as documented in /app/docs/challenge-types.md.
