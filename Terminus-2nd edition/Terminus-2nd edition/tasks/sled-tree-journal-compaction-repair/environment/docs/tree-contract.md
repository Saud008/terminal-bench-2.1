B-tree tables use ORDER 4 fanout (split when a node would hold more than 4 keys). Minimum occupancy after delete is floor((ORDER+1)/2) = 2 keys.

Leaf and internal splits use mid = floor(n/2): left keeps indexes [0, mid), right keeps [mid, n). The promoted separator is the key at index mid. For leaf splits the promoted key also remains as the first entry of the right leaf (B+ style). Do not use ceil((n+1)/2) for the left partition.

Internal nodes store an optional high_key upper bound used by scan-range pruning; high_key must reflect the merged subtree maximum after merge.

Committed keys live in /app/state/committed.json and staging rows live in /app/state/staging.json

Batch apply collapses repeated put keys within one JSONL batch to the last value for that key, applies those puts in ascending key order, then applies every delete in JSONL appearance order. After publish, walk physical_entry_count must equal key_count for the committed table (one physical leaf slot per key).

After delete, any node that falls below minimum occupancy must rebalance before publish completes. Preference order: borrow from the left sibling if it has more than the minimum keys; else borrow from the right sibling if it has more than the minimum; else merge with the left sibling if one exists; else merge with the right sibling. Leaf borrow moves the real sibling entry (not the parent separator value as a substitute key) and then sets the parent separator to the first key of the right sibling. Leaf merge concatenates left and right leaf entries and must not re-insert the parent separator into the merged leaf. When an empty child is removed, drop the correct parent separator (the separator immediately left of the removed child, or the first separator when removing the leftmost child). Empty internal children are removed with that separator rule.
