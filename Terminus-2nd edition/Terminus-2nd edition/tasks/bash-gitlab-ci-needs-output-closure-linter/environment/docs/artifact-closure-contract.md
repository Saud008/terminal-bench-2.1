# Artifact closure contract

When needs declares artifacts true, every path the consumer job references must be reachable through the producer artifacts paths list. Walk transitive required needs chains. Optional need edges do not participate in closure walks.
