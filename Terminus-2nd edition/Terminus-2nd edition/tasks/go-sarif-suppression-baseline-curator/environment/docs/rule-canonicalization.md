# Rule canonicalization

Rule keys drive suppression, deduplication, and drift grouping.

## Canonical rule key

Given tool name, rule_id string, and rules_catalog from policy:

1. Lowercase and trim tool.
2. If rule_id exists in rules_catalog.aliases, replace rule_id with the alias target before further steps.
3. Strip a trailing @vN suffix where N is digits.
4. Strip a trailing /vN suffix where N is digits.
5. Return tool + ":" + normalized rule_id.

Example: semgrep + python.lang.security.audit.exec-detected@v2 becomes semgrep:python.lang.security.audit.exec-detected when aliased.
