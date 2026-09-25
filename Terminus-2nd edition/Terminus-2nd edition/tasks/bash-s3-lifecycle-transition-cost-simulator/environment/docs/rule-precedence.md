# Lifecycle rule precedence

Rules carry integer priority. When multiple rules match an object version, the rule with the **highest** priority wins.

Tag filters use tag_prefixes: each entry maps a tag **key** to a required value prefix. All listed prefixes must match (key present and value starts with prefix).

Specificity tie-break: among equal priority, the rule matching more tag_prefixes wins. Lexicographically smallest rule id breaks remaining ties.

Rules with empty tag_prefixes match every object version.
