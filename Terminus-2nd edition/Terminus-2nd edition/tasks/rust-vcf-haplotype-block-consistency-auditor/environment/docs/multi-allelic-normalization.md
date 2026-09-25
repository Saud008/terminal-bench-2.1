# Multi-allelic normalization

Split the VCF ALT column on comma into ordered alternate alleles. Allele index zero is REF. Allele index one maps to the first ALT token, index two to the second ALT, and so on.

Multi-allelic GT indices must resolve against the split ALT list.
