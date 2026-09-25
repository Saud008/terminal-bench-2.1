# MinHash seed compatibility

Each MinHash row uses coefficients derived from base_seed, row index, and optional permutation salt from TB3_PERM_SALT when set.

For row index r starting at zero: let seed equal base_seed wrapping_mul 0x9E3779B9 wrapping_add r as u64. When TB3_PERM_SALT is non-empty, add the salt byte length as u64 to seed using wrapping add.

Compute a as seed wrapping_mul 6364136223846793005 wrapping_add 1, then force a odd with bitwise or one, then reduce modulo 1000000007. Compute b as seed wrapping_add 1442695040888963407 reduced modulo 1000000007.

Hash each shingle string by iterating bytes with h equals h wrapping_mul 31 wrapping_add byte, starting from zero. Row hash equals a wrapping_mul h wrapping_add b modulo 1000000007.

The signature value at row r is the minimum row hash across all shingles. When no shingles exist, use u64 MAX for that row.
