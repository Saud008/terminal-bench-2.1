# Delegation path constraints

Targets metadata may declare delegations with name, paths, threshold, and keyids.

Path patterns use slash-separated segments. Asterisk matches exactly one segment. Double-asterisk matches zero or more segments greedily.

For each target path, choose the delegation whose matching pattern has the greatest literal character count (wildcards do not count). Ties break by delegation name lexicographic ascending order.

A target is allowed when it matches at least one pattern of the winning delegation. Targets with no matching delegation are rejected with reason no_delegation.

Release single-segment wildcards must not match deeper paths: release/* matches release/app-v1.tar.gz but not release/extra/nested.bin.
