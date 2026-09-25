use crate::export::wrap;
use crate::model::MigrateExport;
use crate::staging;

pub fn publish_migrate(snapshot_path: &str) -> Result<MigrateExport, String> {
    let snap = staging::load(snapshot_path)?;
    let mut doc = MigrateExport::from(snap);
    doc.entities.sort_by(|a, b| b.id.cmp(&a.id));
    Ok(wrap::apply_export_layer(doc))
}
