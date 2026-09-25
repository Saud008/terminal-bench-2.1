# Group-aware holdout split

Assign each example a split role using peer_group:

1. Sort unique peer_group strings ascending.
2. Let g0, g1, ... be that order.
3. Assign group g_i to:
   - train if i % 3 == 0
   - validation if i % 3 == 1
   - test if i % 3 == 2

Never put two examples from the same peer_group into different splits.
