use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CellExport {
    pub text: String,
    pub col: usize,
    pub colspan: usize,
    pub rowspan: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RowExport {
    pub row_index: usize,
    pub cells: Vec<CellExport>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TableExport {
    pub export_version: u32,
    pub source: String,
    pub column_count: usize,
    pub rows: Vec<RowExport>,
}

#[derive(Debug, Clone)]
pub struct RawCell {
    pub text: String,
    pub colspan: usize,
    pub rowspan: usize,
}

#[derive(Debug, Clone)]
pub struct PlacedCell {
    pub text: String,
    pub col: usize,
    pub colspan: usize,
    pub rowspan: usize,
}
