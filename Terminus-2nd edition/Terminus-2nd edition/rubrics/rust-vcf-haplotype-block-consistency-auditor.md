# Platform rubric — rust-vcf-haplotype-block-consistency-auditor

**Task folder:** tasks/rust-vcf-haplotype-block-consistency-auditor/

Agent parses phased genotypes only when GT uses pipe separator, 3
Agent splits multi-allelic ALT fields on comma before allele index mapping, 3
Agent groups phased blocks by CHROM and normalized PS tag together, 3
Agent flags partial missing calls when either GT allele token is dot, 2
Agent orders sample lineage ascending by sample_id from manifest, 2
Agent increments ingest_generation on each materialize for same run id, 2
Agent detects cross-sample phase discordance within a variant row, 3
Agent emits anomaly_id with miss- mix- and disc- templates from consistency-report-fields, 3
Agent includes every phased non-missing sample in phase_discordance sample_ids, 2
Agent writes block edge list JSONL with merge_generation header line, 2
Agent strips TB3_PS_SALT prefix from PS tags before block grouping, 3
Agent computes audit_digest with block_count anomaly_count and block_ids, 3
Agent rebuilds vcfaud after Rust source edits, 2
Agent uses materialize wire-blocks score-anomalies without decoy PCA module, 1
Agent treats slash separated GT as phased when PS tag is present, -3
Agent groups variants by PS tag alone ignoring chromosome, -3
Agent leaves comma joined ALT as single allele in variant catalog, -2
Agent skips missing call detection for dot pipe dot genotypes, -2
Agent sorts sample lineage reverse lexicographic, -2
Agent omits TB3_PS_SALT stripping when env var is set, -2
Agent invents anomaly_id prefixes other than miss- mix- disc-, -3
Agent lists only minority orientation samples for phase_discordance, -2
