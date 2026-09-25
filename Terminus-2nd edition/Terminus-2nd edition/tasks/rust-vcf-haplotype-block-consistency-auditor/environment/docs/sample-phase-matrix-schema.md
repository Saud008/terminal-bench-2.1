# Sample phase matrix schema

vcfaud materialize writes /app/state/sample-phase-matrix/<run-id>.json with run_id, profile, ingest_generation, sample_lineage, and variant_catalog array.

ingest_generation starts at one on first materialize for a run id. Each re-materialize of the same run id increments ingest_generation by one.

Each variant record in variant_catalog includes chrom, pos, ref_allele, alt_alleles array, and genotypes array with sample_id, gt_raw, phased, missing, alleles, and ps_tag.
