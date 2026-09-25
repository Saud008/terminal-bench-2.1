use crate::model::MigrateExport;

pub fn apply_export_layer(mut doc: MigrateExport) -> MigrateExport {
    for ent in &mut doc.entities {
        ent.slot_generation = 0;
    }
    doc
}
