use std::env;

fn home() -> Option<String> {
    env::var("HOME").ok()
}

/// Expands a leading `~/` (or a lone `~`) to `$HOME`. Other values are
/// returned unchanged.
pub fn expand_user(value: &str) -> Option<String> {
    if value == "~" {
        return home();
    }
    match value.strip_prefix("~/") {
        Some(rest) => home().map(|h| format!("{h}/{rest}")),
        None => Some(value.to_string()),
    }
}

/// The excludes file git reads when `core.excludesFile` is not set.
pub fn default_excludes_file() -> Option<String> {
    match env::var("XDG_CONFIG_HOME") {
        Ok(dir) if !dir.is_empty() => Some(format!("{dir}/git/ignore")),
        _ => home().map(|h| format!("{h}/.config/git/ignore")),
    }
}
