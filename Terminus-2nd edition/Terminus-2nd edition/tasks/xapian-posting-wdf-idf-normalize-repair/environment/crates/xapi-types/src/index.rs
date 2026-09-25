            use crate::document::Document;
            use serde::{Deserialize, Serialize};
            use std::collections::BTreeMap;
            use std::fs;
            use std::path::Path;

            #[derive(Debug, Clone, Serialize, Deserialize, Default)]
            pub struct IndexFile {
                pub documents: Vec<Document>,
                pub next_order: u64,
                pub cf: BTreeMap<String, u64>,
            }

            impl IndexFile {
                pub fn load(path: &Path) -> Result<Self, String> {
                    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
                    serde_json::from_str(&raw).map_err(|e| e.to_string())
                }

                pub fn save(path: &Path, file: &Self) -> Result<(), String> {
                    let data = serde_json::to_string_pretty(file).map_err(|e| e.to_string())?;
                    fs::write(path, format!("{data}
")).map_err(|e| e.to_string())
                }

                pub fn doc_count(&self) -> u64 {
                    self.documents.len() as u64
                }
            }
