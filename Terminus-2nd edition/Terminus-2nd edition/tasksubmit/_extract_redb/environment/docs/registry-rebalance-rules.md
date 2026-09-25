# Registry rebalance rules

On this system-administration page-registry control plane, split medians and underflow borrow direction must stay aligned with the rules below.

## Leaf split median

When a leaf holds n entries and must split, let mid = n / 2 using integer division.

- Left child receives entries [0..mid] (exclusive end mid).
- Promoted separator is entry[mid].0 (first key of right child).
- Right child receives entries [mid..].

For odd n this gives floor(n/2) entries on the left. Using ceil(n/2) on the left violates key order after repeated splits.

## Internal split median

When an internal page splits, use the same integer mid = n / 2 rule on separator keys:

- Left internal node holds keys [0..mid] and children [0..mid+1].
- Promoted separator is keys[mid].
- Right internal node holds keys[mid+1..] and children[mid+1..].

Odd key counts must use floor(n/2) on the left, matching leaf split semantics.

## Underflow borrow direction

When a child underflows after delete, borrow from the **left** sibling if that sibling has more than the minimum keys. Only borrow from the right sibling when the left cannot donate.

## Parent underflow

When a child underflows and neither sibling can borrow, merge with a sibling and propagate underflow to the parent internal node. Do not leave a child below minimum without propagating that underflow upward.
