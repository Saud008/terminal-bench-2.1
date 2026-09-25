# Uncertainty budget propagation

## Combined standard uncertainty

combined_standard uncertainty u_c is the root-sum-square of component values:

u_c = sqrt(sum(u_i^2))

Do not sum components linearly.

## Expanded uncertainty

expanded_uncertainty equals combined_standard multiplied by the coverage_factor from caldoss.json (default 2.0).

Dossier publish rows must expose expanded_uncertainty not combined_standard.
