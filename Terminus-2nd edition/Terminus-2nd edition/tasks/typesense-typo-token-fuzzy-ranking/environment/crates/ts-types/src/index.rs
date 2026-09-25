use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::document::Document;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct IndexFile {
    pub documents: Vec<Document>,
    pub token_index: BTreeMap<String, Vec<String>>,
    pub next_order: u64,
}

impl IndexFile {
    pub fn load(path: &Path) -> Result<Self, String> {
        if !path.exists() {
            return Ok(Self::default());
        }
        let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
        serde_json::from_str(&raw).map_err(|e| e.to_string())
    }

    pub fn save(path: &Path, index: &Self) -> Result<(), String> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let data = serde_json::to_string_pretty(index).map_err(|e| e.to_string())?;
        fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
    }

    pub fn doc_count(&self) -> usize {
        self.documents.len()
    }
}
