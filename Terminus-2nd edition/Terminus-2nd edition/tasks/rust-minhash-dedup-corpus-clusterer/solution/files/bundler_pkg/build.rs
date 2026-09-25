use crate::cluster_representative;
use crate::cluster_threshold;
use crate::types::{ClusterGraph, ClusterRecord, SketchIndex};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;

pub fn cluster_run_id(run_id: &str, generation: u32) -> String {
    let body = format!("{run_id}:{generation}");
    format!("grp-{}", &hex::encode(Sha256::digest(body.as_bytes()))[..12])
}

pub fn build_graph(cfg: &crate::types::Config, run_id: &str, floor: f64) -> Result<PathBuf, String> {
    let sketch_path = PathBuf::from(&cfg.sketch_index_dir).join(format!("{run_id}.json"));
    let raw = fs::read_to_string(&sketch_path).map_err(|e| e.to_string())?;
    let sketch: SketchIndex = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let n = sketch.documents.len();
    let mut edges = Vec::new();
    for i in 0..n {
        for j in (i + 1)..n {
            let est = cluster_threshold::estimate_jaccard(
                &sketch.documents[i].signature,
                &sketch.documents[j].signature,
            );
            if cluster_threshold::should_cluster(est, floor) {
                edges.push((i, j));
            }
        }
    }
    let groups = cluster_threshold::cluster_union_find(n, &edges);
    let mut sorted_groups: Vec<Vec<usize>> = groups;
    sorted_groups.sort_by(|a, b| {
        let a_min = a
            .iter()
            .map(|i| sketch.documents[*i].doc_id.as_str())
            .min()
            .unwrap_or("");
        let b_min = b
            .iter()
            .map(|i| sketch.documents[*i].doc_id.as_str())
            .min()
            .unwrap_or("");
        a_min.cmp(b_min)
    });
    let mut clusters = Vec::new();
    for (idx, members) in sorted_groups.iter().enumerate() {
        let doc_ids: Vec<String> = members
            .iter()
            .map(|i| sketch.documents[*i].doc_id.clone())
            .collect();
        let mut sorted_ids = doc_ids.clone();
        sorted_ids.sort();
        let rep = cluster_representative::pick_representative(&sorted_ids);
        let min_est = if members.len() < 2 {
            0.0
        } else {
            let mut best = 1.0f64;
            for a in 0..members.len() {
                for b in (a + 1)..members.len() {
                    let est = cluster_threshold::estimate_jaccard(
                        &sketch.documents[members[a]].signature,
                        &sketch.documents[members[b]].signature,
                    );
                    if est < best {
                        best = est;
                    }
                }
            }
            best
        };
        clusters.push(ClusterRecord {
            cluster_id: format!("c{:03}", idx + 1),
            representative_doc_id: rep,
            member_doc_ids: sorted_ids,
            min_pairwise_estimate: min_est,
        });
    }
    clusters.sort_by(|a, b| a.cluster_id.cmp(&b.cluster_id));
    let graph_path = PathBuf::from(&cfg.cluster_graph_dir).join(format!("{run_id}.json"));
    let prev_gen = if graph_path.exists() {
        let prev: ClusterGraph =
            serde_json::from_str(&fs::read_to_string(&graph_path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        prev.group_generation
    } else {
        0
    };
    let generation = prev_gen + 1;
    let graph = ClusterGraph {
        run_id: run_id.to_string(),
        jaccard_floor: floor,
        group_generation: generation,
        cluster_run_id: cluster_run_id(run_id, generation),
        clusters,
    };
    fs::create_dir_all(&cfg.cluster_graph_dir).map_err(|e| e.to_string())?;
    fs::write(
        &graph_path,
        serde_json::to_string_pretty(&graph).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    Ok(graph_path)
}
