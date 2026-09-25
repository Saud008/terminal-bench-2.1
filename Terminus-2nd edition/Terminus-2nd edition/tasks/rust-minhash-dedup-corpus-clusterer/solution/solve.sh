#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/lexfold_pkg/unicode.rs <<'EOF'
use unicode_normalization::UnicodeNormalization;

pub fn normalize_unicode(raw: &str) -> String {
    raw.nfkc().collect::<String>().to_lowercase()
}
EOF

cat > /app/lexfold_pkg/punct.rs <<'EOF'
pub fn strip_punctuation(token: &str) -> String {
    const STRIP: &[char] = &['.', ',', '!', '?', ';', ':', '\u{27}', '"', '(', ')', '[', ']', '{', '}'];
    token.trim_matches(STRIP).to_string()
}

pub fn normalize_tokens(raw: &str) -> Vec<String> {
    let mut out = Vec::new();
    for piece in raw.split_whitespace() {
        let t = strip_punctuation(piece);
        if !t.is_empty() {
            out.push(t);
        }
    }
    out
}
EOF

cat > /app/wingram_pkg/window.rs <<'EOF'
pub fn word_shingles(tokens: &[String], k: usize) -> Vec<String> {
    if tokens.len() < k {
        return Vec::new();
    }
    let mut out = Vec::new();
    for i in 0..=tokens.len() - k {
        out.push(tokens[i..i + k].join(" "));
    }
    out
}
EOF

cat > /app/rowmix_pkg/permutation.rs <<'EOF'
const PRIME: u64 = 1_000_000_007;

pub fn row_coefficients(base_seed: u64, row: usize, salt: &str) -> (u64, u64) {
    let mut seed = base_seed.wrapping_mul(0x9E3779B9).wrapping_add(row as u64);
    if !salt.is_empty() {
        seed = seed.wrapping_add(salt.len() as u64);
    }
    let a = seed.wrapping_mul(6364136223846793005).wrapping_add(1) | 1;
    let b = seed.wrapping_add(1442695040888963407);
    (a % PRIME, b % PRIME)
}

pub fn hash_token(token: &str, a: u64, b: u64) -> u64 {
    let mut h: u64 = 0;
    for byte in token.as_bytes() {
        h = h.wrapping_mul(31).wrapping_add(u64::from(*byte));
    }
    (a.wrapping_mul(h).wrapping_add(b)) % PRIME
}
EOF

cat > /app/rowmix_pkg/vector.rs <<'EOF'
use crate::hash_permutation;

pub fn minhash_signature(shingles: &[String], base_seed: u64, num_hashes: usize, salt: &str) -> Vec<u64> {
    let mut sig = vec![u64::MAX; num_hashes];
    if shingles.is_empty() {
        return sig;
    }
    for row in 0..num_hashes {
        let (a, b) = hash_permutation::row_coefficients(base_seed, row, salt);
        let mut best = u64::MAX;
        for sh in shingles {
            let h = hash_permutation::hash_token(sh, a, b);
            if h < best {
                best = h;
            }
        }
        sig[row] = best;
    }
    sig
}
EOF

cat > /app/ufmerge_pkg/threshold.rs <<'EOF'
pub fn estimate_jaccard(sig_a: &[u64], sig_b: &[u64]) -> f64 {
    if sig_a.len() != sig_b.len() || sig_a.is_empty() {
        return 0.0;
    }
    let matches = sig_a.iter().zip(sig_b).filter(|(a, b)| a == b).count();
    matches as f64 / sig_a.len() as f64
}

pub fn should_cluster(estimate: f64, floor: f64) -> bool {
    estimate >= floor
}

pub fn cluster_union_find(n: usize, edges: &[(usize, usize)]) -> Vec<Vec<usize>> {
    let mut parent: Vec<usize> = (0..n).collect();
    fn find(parent: &mut [usize], x: usize) -> usize {
        if parent[x] != x {
            parent[x] = find(parent, parent[x]);
        }
        parent[x]
    }
    for &(a, b) in edges {
        let ra = find(&mut parent, a);
        let rb = find(&mut parent, b);
        if ra != rb {
            parent[rb] = ra;
        }
    }
    let mut buckets: std::collections::BTreeMap<usize, Vec<usize>> = std::collections::BTreeMap::new();
    for i in 0..n {
        buckets.entry(find(&mut parent, i)).or_default().push(i);
    }
    buckets.into_values().collect()
}
EOF

cat > /app/ufmerge_pkg/representative.rs <<'EOF'
pub fn pick_representative(doc_ids: &[String]) -> String {
    doc_ids.iter().min().cloned().unwrap_or_default()
}
EOF

sed -i 's/scan_generation: prev_gen,/scan_generation: prev_gen + 1,/' /app/snapcache_pkg/write.rs

cat > /app/bundler_pkg/build.rs <<'ORACLE_PART2'
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
ORACLE_PART2

cat > /app/sealrep_pkg/report.rs <<'ORACLE_PART3'
use crate::types::{ClusterGraph, ProvenanceCluster, ProvenanceReport, SketchIndex};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

pub fn audit_digest(report: &ProvenanceReport) -> String {
    let member_lists: Vec<Vec<String>> = report
        .clusters
        .iter()
        .map(|c| c.member_doc_ids.clone())
        .collect();
    let body = serde_json::json!({
        "cluster_count": report.cluster_count,
        "cluster_run_id": report.cluster_run_id,
        "jaccard_floor": report.jaccard_floor,
        "member_lists": member_lists,
        "run_id": report.run_id,
        "singleton_count": report.singleton_count,
        "total_documents": report.total_documents,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

pub fn build_report(cfg: &crate::types::Config, run_id: &str) -> Result<ProvenanceReport, String> {
    let sketch: SketchIndex = serde_json::from_str(
        &fs::read_to_string(PathBuf::from(&cfg.sketch_index_dir).join(format!("{run_id}.json")))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let graph: ClusterGraph = serde_json::from_str(
        &fs::read_to_string(PathBuf::from(&cfg.cluster_graph_dir).join(format!("{run_id}.json")))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    let path_by_id: BTreeMap<String, String> = sketch
        .documents
        .iter()
        .map(|d| (d.doc_id.clone(), d.source_path.clone()))
        .collect();

    let mut clusters = Vec::new();
    for c in &graph.clusters {
        let mut member_doc_ids = c.member_doc_ids.clone();
        member_doc_ids.sort();
        let source_paths: Vec<String> = member_doc_ids
            .iter()
            .filter_map(|id| path_by_id.get(id).cloned())
            .collect();
        clusters.push(ProvenanceCluster {
            cluster_id: c.cluster_id.clone(),
            representative_doc_id: c.representative_doc_id.clone(),
            member_doc_ids,
            source_paths,
            min_pairwise_estimate: c.min_pairwise_estimate,
        });
    }
    clusters.sort_by(|a, b| a.cluster_id.cmp(&b.cluster_id));

    let singleton_count = clusters.iter().filter(|c| c.member_doc_ids.len() == 1).count() as u32;
    let mut report = ProvenanceReport {
        run_id: run_id.to_string(),
        cluster_run_id: graph.cluster_run_id.clone(),
        jaccard_floor: graph.jaccard_floor,
        total_documents: sketch.documents.len() as u32,
        cluster_count: clusters.len() as u32,
        singleton_count,
        clusters,
        audit_digest: String::new(),
    };
    report.audit_digest = audit_digest(&report);
    Ok(report)
}

pub fn write_report(cfg: &crate::types::Config, run_id: &str, output: &Path) -> Result<(), String> {
    let report = build_report(cfg, run_id)?;
    fs::write(
        output,
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}
ORACLE_PART3

/usr/local/cargo/bin/cargo build --release --locked
