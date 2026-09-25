use crate::canonicalize::import_order::canonical_imports;
use crate::parse::type_index::{apply_tb3_offset, resolve_type_index};
use crate::types::{ImportRow, LedgerComponent, TypeAlias};

pub fn import_reorder_digest(comp: &LedgerComponent) -> String {
    canonical_digest_hex(&comp.imports, &comp.aliases)
}

pub fn canonical_digest_bytes(imports: &[ImportRow], aliases: &[TypeAlias]) -> Vec<u8> {
    let ordered = canonical_imports(imports);
    let mut buf = Vec::new();
    for row in &ordered {
        let module = row.module.as_bytes();
        let name = row.name.as_bytes();
        buf.push(module.len() as u8);
        buf.extend_from_slice(module);
        buf.push(name.len() as u8);
        buf.extend_from_slice(name);
        let mt = apply_tb3_offset(resolve_type_index(row.type_local, aliases));
        buf.extend_from_slice(&mt.to_le_bytes());
    }
    buf
}

pub fn canonical_digest_hex(imports: &[ImportRow], aliases: &[TypeAlias]) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(canonical_digest_bytes(imports, aliases));
    hex::encode(hasher.finalize())
}
