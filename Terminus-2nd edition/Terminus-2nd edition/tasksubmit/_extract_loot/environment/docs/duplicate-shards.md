# Duplicate item conversion

When processing a pull, if item_id is already present in the player inventory list, do not grant the item again. Instead add duplicate_shards[rarity] from the season config to the player shard balance and record a duplicate_shard audit entry.

First acquisition of an item_id appends it to inventory sorted lexicographically after each grant. Duplicate detection is exact string match on item_id.
