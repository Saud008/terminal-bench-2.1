use crate::model::LayoutManifest;
use anyhow::{bail, Result};

pub fn validate_manifest(manifest: &LayoutManifest) -> Result<()> {
    if manifest.from_version >= manifest.to_version {
        bail!("to_version must exceed from_version");
    }
    if manifest.migration_steps.is_empty() {
        bail!("migration_steps required");
    }
    let mut seen = std::collections::HashSet::new();
    for step in &manifest.migration_steps {
        if !seen.insert(step.order) {
            bail!("duplicate migration order {}", step.order);
        }
    }
    Ok(())
}
