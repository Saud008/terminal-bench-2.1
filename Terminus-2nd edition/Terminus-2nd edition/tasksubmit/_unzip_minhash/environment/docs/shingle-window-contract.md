# Shingle window contract

Word shingles use the normalized token sequence from token normalization.

Let k be shingle_k from the active minclus configuration (default 5). Emit one shingle for each contiguous window of exactly k tokens. Join tokens within a window with a single ASCII space. Do not emit windows wider or narrower than k tokens.

When fewer than k tokens exist after normalization, emit zero shingles.
