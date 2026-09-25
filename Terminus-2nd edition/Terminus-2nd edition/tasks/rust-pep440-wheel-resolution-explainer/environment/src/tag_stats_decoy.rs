pub fn wrap_tag_metric(tag: &str, score: u64) -> String {
    format!("tag_metric:{tag}={score}")
}
