use crate::types::{BlockAnomaly, VariantRecord};

pub fn detect_anomalies(variants: &[VariantRecord]) -> Vec<BlockAnomaly> {
    let mut anomalies = Vec::new();
    for v in variants {
        for gt in &v.genotypes {
            if gt.missing {
                anomalies.push(BlockAnomaly {
                    anomaly_id: format!("miss-{}-{}", gt.sample_id, v.pos),
                    chrom: v.chrom.clone(),
                    ps_tag: gt.ps_tag.clone(),
                    anomaly_type: "missing_call".to_string(),
                    sample_ids: vec![gt.sample_id.clone()],
                    variant_positions: vec![v.pos],
                });
            }
        }
    }
    anomalies
}
