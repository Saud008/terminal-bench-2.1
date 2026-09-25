# Principal precedence

AuthorizedPrincipalsFile lines are evaluated after Match blocks select a scope-specific principals file.

Deny principals prefixed with exclamation apply before allow lines. Among matching allow lines, lower rank numbers win (more specific principals beat wildcards). When a Match block selects a non-global scope, only principals from that scope file participate. When no Match block applies, only the global principals file participates.

Principal lines use fnmatch semantics with case-insensitive host and user matching in Match blocks only; principal pattern matching is case sensitive.
