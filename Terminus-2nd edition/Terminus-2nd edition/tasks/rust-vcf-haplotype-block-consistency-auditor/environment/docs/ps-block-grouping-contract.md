# Phase-set block grouping contract

Group variants into phased blocks using composite key CHROM colon PS tag from each genotype PS field.

When TB3_PS_SALT is set, strip that prefix from PS tags before grouping. After removing the salt prefix, also drop any leading dash from the remaining PS tag. For example with TB3_PS_SALT set to SALT, the tag SALT-77 normalizes to 77. Two variants belong to the same block only when both CHROM and normalized PS tag match.

Block ids are formatted blk followed by three decimal digits in discovery order sorted by composite key ascending.
