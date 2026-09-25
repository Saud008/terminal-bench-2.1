use std::fs;
use std::path::Path;

use crate::attest::digest::import_reorder_digest;
use crate::canonicalize::import_order::canonical_imports;
use crate::ledger::load_ledger;
use crate::parse::type_index::{apply_tb3_offset, resolve_type_index};
use crate::resolve::alias_closure::resolve_surfaces;
use crate::types::{
    AttestImport, AttestationDoc, ComponentAttestation, SurfaceExport,
};

pub fn attest_export(ledger_path: &str, export_path: &str) -> Result<(), String> {
    let ledger = load_ledger(ledger_path)?;
    let mut components = Vec::new();
    for comp in &ledger.components {
        let ordered = canonical_imports(&comp.imports);
        let imports: Vec<AttestImport> = ordered
            .iter()
            .map(|row| AttestImport {
                module: row.module.clone(),
                name: row.name.clone(),
                type_index: apply_tb3_offset(resolve_type_index(row.type_local, &comp.aliases)),
            })
            .collect();
        let surfaces: Vec<SurfaceExport> = resolve_surfaces(comp)
            .into_iter()
            .map(|(outer, resolved_leaf)| SurfaceExport {
                outer,
                resolved_leaf,
            })
            .collect();
        let import_reorder_digest = import_reorder_digest(comp);
        components.push(ComponentAttestation {
            name: comp.filename.clone(),
            imports,
            surface_exports: surfaces,
            import_reorder_digest,
        });
    }
    let doc = AttestationDoc {
        ingest_seq: ledger.ingest_seq,
        components,
    };
    let parent = Path::new(export_path).parent().unwrap_or(Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    fs::write(export_path, format!("{pretty}\n")).map_err(|e| e.to_string())
}
