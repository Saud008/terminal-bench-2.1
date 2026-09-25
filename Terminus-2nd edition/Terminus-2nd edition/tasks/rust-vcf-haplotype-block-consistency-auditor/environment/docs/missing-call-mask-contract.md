# Missing-call mask contract

Mark a genotype missing when GT is ./. or .|. or any allele token is a lone dot.

Partial missing calls with one dot allele in a phased or unphased GT count as missing for anomaly detection.

Emit one missing_call anomaly per affected sample at each variant row. When two samples in the same row have missing genotypes, export two separate anomalies, each listing only that sample in sample_ids. The anomaly_id for each missing_call is `miss-{sample_id}-{pos}` as defined in consistency-report-fields.md.
