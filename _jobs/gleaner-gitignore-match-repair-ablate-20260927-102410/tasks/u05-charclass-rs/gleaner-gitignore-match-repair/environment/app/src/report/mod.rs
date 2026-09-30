//! Output formatting for both commands.

use crate::ignore::Verdict;

/// One `check` line: `SOURCE:LINE:PATTERN<TAB>PATH`, or `::<TAB>PATH` when
/// no pattern matched.
pub fn check_line(path: &str, verdict: &Verdict) -> String {
    match verdict {
        Verdict::Matched(hit) => format!("{}:{}:{}\t{}\n", hit.source, hit.line, hit.text, path),
        Verdict::NoMatch => format!("::\t{path}\n"),
    }
}

pub fn list_lines(paths: &[String]) -> String {
    let mut out = String::with_capacity(paths.iter().map(|p| p.len() + 1).sum());
    for path in paths {
        out.push_str(path);
        out.push('\n');
    }
    out
}
