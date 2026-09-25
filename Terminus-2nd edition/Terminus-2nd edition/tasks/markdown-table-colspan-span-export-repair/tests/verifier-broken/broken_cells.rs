/// Split a pipe row into cell bodies per the extension contract.
pub fn split_row(line: &str) -> Vec<String> {
    let trimmed = line.trim();
    let inner = trimmed
        .strip_prefix('|')
        .and_then(|s| s.strip_suffix('|'))
        .unwrap_or(trimmed);
    inner
        .split('|')
        .map(|part| part.trim().to_string())
        .collect()
}
