# Route match precedence

Exact path matches outrank prefix matches.

Among prefix matches, longer prefix length wins.

When still tied, higher precedence integer wins.

Normalize collapses to one winning route per cluster using these rules.
