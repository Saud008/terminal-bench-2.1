use std::path::{Path, PathBuf};

use crate::voyage_err::SegmentError;

pub fn resolve_input(input: &str) -> Result<PathBuf, SegmentError> {
    if let Ok(base) = std::env::var("TB3_AIS_DIR") {
        if Path::new(&base).is_absolute() {
            let name = Path::new(input)
                .file_name()
                .and_then(|s| s.to_str())
                .ok_or_else(|| SegmentError::Parse("input must be basename with TB3_AIS_DIR".into()))?;
            return Ok(PathBuf::from(base).join(name));
        }
    }
    Ok(PathBuf::from(input))
}
