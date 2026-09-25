//! TB3_TRACE_DIR resolution for ingest and simulate CLI paths.

use std::path::{Path, PathBuf};

/// When TB3_TRACE_DIR is set, a trace argument with no parent directory joins under it.
pub fn resolve_trace_path(trace_path: &Path) -> PathBuf {
    if let Ok(dir) = std::env::var("TB3_TRACE_DIR") {
        if !dir.is_empty() {
            let parentless = trace_path
                .parent()
                .map(|p| p.as_os_str().is_empty())
                .unwrap_or(true);
            if parentless {
                return PathBuf::from(dir).join(trace_path);
            }
        }
    }
    trace_path.to_path_buf()
}
