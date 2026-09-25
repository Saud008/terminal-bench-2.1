pub fn region_allowed(region: &str, allowed: &[String]) -> bool {
    allowed.iter().any(|r| r == region)
}
