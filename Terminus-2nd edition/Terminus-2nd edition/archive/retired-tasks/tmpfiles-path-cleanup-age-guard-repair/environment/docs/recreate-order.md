# Recreate sequencing

z recreate lines must run only after every pending age-based removal triggered by r! lines whose GLOB matches paths under the same directory prefix as the z PATH has completed in the current apply pass.

Rules are processed in file order. When a z line appears before r! lines that target paths under its prefix, recreate must wait until those later r! lines have finished removing eligible paths (or those paths fail the age gate).

Directory prefix means: for z PATH /var/tmp/state, wait until no eligible r! removal remains anywhere under /var/tmp/state/ (including the path itself if matched).

Recreate among z lines that pass the gate runs when encountered in rule order. Running z while eligible age removals under the prefix are still pending is incorrect.
