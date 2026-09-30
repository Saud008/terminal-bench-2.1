/// Sorts listed paths directory by directory, comparing one path component
/// at a time.
pub fn sort_paths(mut paths: Vec<String>) -> Vec<String> {
    paths.sort_unstable_by(|a, b| a.split('/').cmp(b.split('/')));
    paths
}
