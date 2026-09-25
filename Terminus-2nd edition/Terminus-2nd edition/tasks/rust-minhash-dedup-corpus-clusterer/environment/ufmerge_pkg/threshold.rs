pub fn estimate_jaccard(sig_a: &[u64], sig_b: &[u64]) -> f64 {
    if sig_a.len() != sig_b.len() || sig_a.is_empty() {
        return 0.0;
    }
    let matches = sig_a.iter().zip(sig_b).filter(|(a, b)| a == b).count();
    let n = sig_a.len() as f64;
    matches as f64 / (2.0 * n - matches as f64)
}

pub fn should_cluster(estimate: f64, floor: f64) -> bool {
    estimate > floor
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
    let mut groups: Vec<Vec<usize>> = Vec::new();
    for i in 0..n {
        if parent[i] == i {
            groups.push(vec![i]);
        }
    }
    groups
}
