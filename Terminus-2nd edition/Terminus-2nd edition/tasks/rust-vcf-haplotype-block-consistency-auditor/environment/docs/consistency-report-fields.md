# Consistency report fields

vcfaud score-anomalies writes JSON with run_id, block_count, anomaly_count, blocks, anomalies, and audit_digest.

Anomalies sort by anomaly_id ascending. Each anomaly includes anomaly_id, chrom, ps_tag, anomaly_type, sample_ids, and variant_positions. Recognized anomaly_type values are missing_call, phase_set_mixed, and phase_discordance.

## anomaly_id formats

anomaly_id strings use these exact templates (no other prefixes or extra path segments):

- missing_call: `miss-{sample_id}-{pos}`
- phase_set_mixed: `mix-{sample_id}-{pos}`
- phase_discordance: `disc-{chrom}-{pos}`

`{pos}` is the integer VCF POS for that variant row, rendered in decimal with no zero padding.

## Anomaly emission rules

**missing_call.** Emit one anomaly per affected sample at each variant row where the genotype is missing under the missing-call mask contract. sample_ids is a one-element list containing that sample_id. variant_positions is a one-element list containing that POS. ps_tag is that sample's PS field at the row (empty string when absent).

**phase_set_mixed.** Emit one anomaly per affected sample at each variant row where the genotype has a non-empty PS tag, is not missing, and is unphased (slash separator). Do not collapse multiple affected samples into a single block-level anomaly. sample_ids is a one-element list containing that sample_id. variant_positions is a one-element list containing that POS. ps_tag is that sample's PS field at the row.

**phase_discordance.** At each variant row, consider genotypes that are phased and not missing. When two or more such genotypes are present and their allele-index tuples are not all identical, emit exactly one phase_discordance anomaly for that row. anomaly_id is `disc-{chrom}-{pos}`. sample_ids lists every phased non-missing sample at that row (not only minority orientations), sorted ascending. variant_positions is a one-element list containing that POS. ps_tag is the PS tag from the first phased non-missing genotype in sample iteration order for that row.

audit_digest is SHA256 hex of compact JSON with keys anomaly_count, block_count, block_ids, run_id. block_ids is sorted block_id strings from blocks. The digest uses the same hashlib SHA256 construction as independent verifier references.

block_count equals blocks length. anomaly_count equals anomalies length.
