use std::fs;
use std::path::Path;

use anyhow::{Context, Result};

use crate::types::FixtureInput;

pub fn load_fixtures(dir: &Path) -> Result<Vec<FixtureInput>> {
    let mut out = Vec::new();
    for entry in fs::read_dir(dir).context("read fixture dir")? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) != Some("json") {
            continue;
        }
        let text = fs::read_to_string(&path)?;
        let fixture: FixtureInput = serde_json::from_str(&text)
            .with_context(|| format!("parse {}", path.display()))?;
        out.push(fixture);
    }
    out.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(out)
}
