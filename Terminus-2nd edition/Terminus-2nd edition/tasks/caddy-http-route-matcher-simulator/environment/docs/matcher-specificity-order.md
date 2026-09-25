# Matcher specificity order

Route matchers are evaluated against the staged route table. A route matches only when every matcher block in its match array succeeds for the request.

Among all matching routes in the same group, the winner is the route with the highest specificity score, not the lowest array index. When two routes tie on score, the lower source index wins.

Specificity scoring:

- Exact path match (no trailing wildcard): 30 points per pattern
- Prefix path match (pattern ends with asterisk): 10 points per pattern
- path_regexp matcher present: 20 points per pattern
- header matcher map: 15 points per header key
- method matcher: 5 points per listed method

Array order alone must never override a higher-scoring matching route.
