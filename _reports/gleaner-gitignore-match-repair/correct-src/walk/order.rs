/// Sorts listed paths the way `git ls-files` prints them: by the bytes of
/// the whole relative path, so `a-b` comes before `a/b` and `a/b` before
/// `a0`.
pub fn sort_paths(mut paths: Vec<String>) -> Vec<String> {
    paths.sort_unstable();
    paths
}
