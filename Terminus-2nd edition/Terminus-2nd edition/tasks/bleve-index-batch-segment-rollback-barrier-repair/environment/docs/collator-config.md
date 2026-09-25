# Collator Configuration

Collation rules are loaded from /app/config/collator.json.

The collator config provides a locale and a weighted key_order list.

Export `ordered_keys` sorting rules:
1. Keys present in `key_order` sort by their configured rank (lower index earlier).
2. Keys absent from `key_order` sort **after every listed key**, using an effective rank greater than any listed rank.
3. Ties (same rank, including among unlisted keys) break by lexicographic UTF-8 order of the key string.

Do not collapse unlisted keys onto rank 0 or any other listed rank. Do not use raw byte-order alone when a collator config is present.

Every committed batch ingested through blevectl must use the same collation rules at export time.
