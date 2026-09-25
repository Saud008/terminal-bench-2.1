pub fn rank_regions(regions: &[String]) -> Vec<String> {
    let mut out = regions.to_vec();
    out.sort();
    out.reverse();
    out
}
