use std::collections::BTreeMap;

use crate::types::{CollisionCluster, DemuxEntry};

pub fn build_clusters(entries: &[DemuxEntry]) -> Vec<CollisionCluster> {
    let mut groups: BTreeMap<(String, String), Vec<String>> = BTreeMap::new();
    for entry in entries {
        groups
            .entry((entry.sample_id.clone(), entry.canonical_umi.clone()))
            .or_default()
            .push(entry.pair_id.clone());
    }

    let mut clusters = Vec::new();
    for ((sample_id, canonical_umi), mut pair_ids) in groups {
        pair_ids.sort();
        let cluster_id = pair_ids
            .iter()
            .map(|pid| {
                entries
                    .iter()
                    .find(|e| &e.pair_id == pid)
                    .map(|e| e.canonical_umi.clone())
                    .unwrap_or_default()
            })
            .min()
            .unwrap_or_else(|| canonical_umi.clone());
        clusters.push(CollisionCluster {
            cluster_id,
            sample_id,
            canonical_umi,
            pair_ids,
        });
    }
    clusters.sort_by(|a, b| a.cluster_id.cmp(&b.cluster_id));
    clusters
}
