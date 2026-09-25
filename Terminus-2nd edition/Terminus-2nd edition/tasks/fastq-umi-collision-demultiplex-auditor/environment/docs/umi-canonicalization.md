# UMI canonicalization

Canonical UMIs are derived per mate before duplicate-family clustering.

For R1 the canonical mate UMI is the umi_length window rotated left by the lane seed_shift plus any TB3_UMI_SEED_SHIFT runtime offset.

For R2 the raw umi_length window is reverse-complemented first, then rotated left by the same total shift.

The pair canonical_umi stored in the demux ledger is the lexicographically smaller of the R1 and R2 canonical mate strings.

Rotation moves the first k bases to the end without altering length. Reverse complement follows IUPAC DNA mapping with N preserved.
