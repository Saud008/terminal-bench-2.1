use crate::types::{BlockAnomaly, VariantRecord};
use std::collections::BTreeSet;

pub fn detect_anomalies(variants: &[VariantRecord]) -> Vec<BlockAnomaly> {
    let mut anomalies = Vec::new();
    for v in variants {
        let phased: Vec<_> = v
            .genotypes
            .iter()
            .filter(|g| g.phased && !g.missing)
            .collect();
        if phased.len() >= 2 {
            let mut patterns = BTreeSet::new();
            for g in &phased {
                patterns.insert(g.alleles.clone());
            }
            if patterns.len() > 1 {
                let mut sample_ids: Vec<String> =
                    phased.iter().map(|g| g.sample_id.clone()).collect();
                sample_ids.sort();
                anomalies.push(BlockAnomaly {
                    anomaly_id: format!("disc-{}-{}", v.chrom, v.pos),
                    chrom: v.chrom.clone(),
                    ps_tag: phased[0].ps_tag.clone(),
                    anomaly_type: "phase_discordance".to_string(),
                    sample_ids,
                    variant_positions: vec![v.pos],
                });
            }
        }
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
            } else if !gt.phased && !gt.ps_tag.is_empty() {
                anomalies.push(BlockAnomaly {
                    anomaly_id: format!("mix-{}-{}", gt.sample_id, v.pos),
                    chrom: v.chrom.clone(),
                    ps_tag: gt.ps_tag.clone(),
                    anomaly_type: "phase_set_mixed".to_string(),
                    sample_ids: vec![gt.sample_id.clone()],
                    variant_positions: vec![v.pos],
                });
            }
        }
    }
    anomalies.sort_by(|a, b| a.anomaly_id.cmp(&b.anomaly_id));
    anomalies
}
