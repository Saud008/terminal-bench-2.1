use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ImportRow {
    pub module: String,
    pub name: String,
    pub type_local: u16,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TypeAlias {
    pub local: u16,
    pub module_type: u16,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WireExport {
    pub kind: u8,
    pub name: String,
    pub instance_target: Option<u16>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReexportEdge {
    pub outer: String,
    pub via_instance: u16,
    pub inner: String,
}

#[derive(Clone, Debug)]
pub struct ParsedComponent {
    pub filename: String,
    pub raw: Vec<u8>,
    pub imports: Vec<ImportRow>,
    pub aliases: Vec<TypeAlias>,
    pub export_section_len: u32,
    pub exports: Vec<WireExport>,
    pub reexports: Vec<ReexportEdge>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LedgerComponent {
    pub filename: String,
    pub raw: Vec<u8>,
    pub imports: Vec<ImportRow>,
    pub aliases: Vec<TypeAlias>,
    pub export_section_len: u32,
    pub exports: Vec<WireExport>,
    pub reexports: Vec<ReexportEdge>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ImportAliasLedger {
    pub ingest_seq: u32,
    pub components: Vec<LedgerComponent>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AttestImport {
    pub module: String,
    pub name: String,
    pub type_index: u16,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SurfaceExport {
    pub outer: String,
    pub resolved_leaf: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ComponentAttestation {
    pub name: String,
    pub imports: Vec<AttestImport>,
    pub surface_exports: Vec<SurfaceExport>,
    pub import_reorder_digest: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AttestationDoc {
    pub ingest_seq: u32,
    pub components: Vec<ComponentAttestation>,
}
