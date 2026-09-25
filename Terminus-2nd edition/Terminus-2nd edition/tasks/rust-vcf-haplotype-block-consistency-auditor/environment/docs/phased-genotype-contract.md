# Phased genotype contract

Genotypes use GT strings with pipe for phased calls and slash for unphased calls.

A genotype is phased only when the GT field contains the pipe separator. Slash-separated genotypes are unphased even when a PS tag is present.

Parse allele indices from phased GT by splitting on pipe. Parse unphased GT by splitting on slash. Dot tokens are missing alleles.

When a genotype has a non-empty PS tag, is not missing, and uses the slash separator, emit a phase_set_mixed anomaly for that sample at that POS with anomaly_id `mix-{sample_id}-{pos}` (see consistency-report-fields.md).
