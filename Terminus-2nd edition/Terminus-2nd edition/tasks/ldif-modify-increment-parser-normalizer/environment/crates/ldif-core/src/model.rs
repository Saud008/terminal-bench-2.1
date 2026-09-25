//! Parsed LDIF values and apply output shapes.
//!
//! `ChangeRecord`, `ModifyOp`, and the serde export structs are a stable public
//! API. Do not add or remove fields. Parser and apply behavior changes belong
//! in those modules only.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ApplyStats {
    pub records_total: u32,
    pub records_applied: u32,
    pub records_skipped: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExportEntry {
    pub dn: String,
    pub attributes: BTreeMap<String, Vec<String>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ApplyExport {
    pub seed: String,
    pub stats: ApplyStats,
    pub entries: Vec<ExportEntry>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuditOperation {
    pub seq: u32,
    pub dn: String,
    pub changetype: String,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuditQuery {
    pub seed: String,
    pub operations: Vec<AuditOperation>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChangeType {
    Add,
    Modify,
    Delete,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChangeRecord {
    pub dn: String,
    pub changetype: ChangeType,
    pub attributes: BTreeMap<String, Vec<String>>,
    pub modify_ops: Vec<ModifyOp>,
}

impl ChangeRecord {
    pub fn add(dn: impl Into<String>, attributes: BTreeMap<String, Vec<String>>) -> Self {
        Self {
            dn: dn.into(),
            changetype: ChangeType::Add,
            attributes,
            modify_ops: Vec::new(),
        }
    }

    pub fn modify(dn: impl Into<String>, modify_ops: Vec<ModifyOp>) -> Self {
        Self {
            dn: dn.into(),
            changetype: ChangeType::Modify,
            attributes: BTreeMap::new(),
            modify_ops,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ModifyKind {
    Add,
    Delete,
    Replace,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ModifyOp {
    pub kind: ModifyKind,
    pub attr: String,
    pub values: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AuditRow {
    pub seq: u32,
    pub dn: String,
    pub changetype: String,
    pub detail: String,
}
