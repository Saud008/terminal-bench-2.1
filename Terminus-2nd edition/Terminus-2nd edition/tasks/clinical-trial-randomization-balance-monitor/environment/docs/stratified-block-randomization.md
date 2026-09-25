# Stratified block randomization

Stratification bucket keys use canonical sorted JSON of factor maps. Block assignment seeds from sha256 of trial_id, stratum_id, and seed_salt. Block sizes cycle through the protocol block_sizes array. Each block emits a random permutation of arms with equal allocation.
