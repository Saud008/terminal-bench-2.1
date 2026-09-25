# Fabric batch lineage

batches.json contains batches array entries with batch_id, parent_batch_id nullable, recipe_name, created_at_epoch, target_lab nullable object with L a b.

When target_lab is null, walk parent_batch_id until a batch with non-null target_lab is found and inherit that anchor for correlation.
