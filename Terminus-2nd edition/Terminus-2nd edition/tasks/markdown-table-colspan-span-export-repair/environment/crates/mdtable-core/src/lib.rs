pub mod error;
pub mod export;
pub mod model;
pub mod parse;
pub mod snapshot;
pub mod span;

pub use error::TableError;
pub use model::{PlacedCell, RawCell, TableExport};

use std::path::Path;

use model::{CellExport, RowExport};
use snapshot::write_grid_snapshot;

pub fn export_json(input: &Path, output: &Path) -> anyhow::Result<TableExport> {
    let doc = prepare_export(input)?;
    write_grid_snapshot(&doc)?;
    export::publish_json(output)
}

pub fn export_html(input: &Path, output: &Path) -> anyhow::Result<()> {
    let doc = prepare_export(input)?;
    write_grid_snapshot(&doc)?;
    export::publish_html(output)
}

pub fn publish_json(output: &Path) -> anyhow::Result<TableExport> {
    export::publish_json(output)
}

pub fn publish_html(output: &Path) -> anyhow::Result<()> {
    export::publish_html(output)
}

fn prepare_export(input: &Path) -> anyhow::Result<TableExport> {
    let content = std::fs::read_to_string(input)?;
    let raw = parse_table_block(&content)
        .ok_or_else(|| TableError::NoTable(input.display().to_string()))?;
    let (placed, column_count) = span::place_grid(&raw);
    Ok(build_doc(input, placed, column_count))
}

fn build_doc(input: &Path, placed: Vec<Vec<PlacedCell>>, column_count: usize) -> TableExport {
    TableExport {
        export_version: 1,
        source: input.to_string_lossy().replace('\\', "/"),
        column_count,
        rows: placed
            .into_iter()
            .enumerate()
            .map(|(idx, row)| RowExport {
                row_index: idx,
                cells: row
                    .into_iter()
                    .map(|c| CellExport {
                        text: c.text,
                        col: c.col,
                        colspan: c.colspan,
                        rowspan: c.rowspan,
                    })
                    .collect(),
            })
            .collect(),
    }
}

fn parse_table_block(content: &str) -> Option<Vec<Vec<RawCell>>> {
    parse::parse_table_block(content)
}
