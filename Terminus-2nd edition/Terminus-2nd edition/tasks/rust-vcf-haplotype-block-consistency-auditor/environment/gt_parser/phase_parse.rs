pub fn is_phased(gt: &str) -> bool {
    gt.contains('|') || gt.contains('/')
}

pub fn parse_alleles(gt: &str) -> Vec<u32> {
    let sep = if gt.contains('|') { '|' } else { '/' };
    gt.split(sep)
        .filter_map(|p| {
            if p == "." {
                None
            } else {
                p.parse().ok()
            }
        })
        .collect()
}
