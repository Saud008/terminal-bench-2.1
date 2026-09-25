pub fn is_missing(gt: &str) -> bool {
    if gt == "./." || gt == ".|." {
        return true;
    }
    let sep = if gt.contains('|') { '|' } else { '/' };
    gt.split(sep).any(|p| p == ".")
}
