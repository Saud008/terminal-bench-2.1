use std::path::Path;

use crate::model::TableExport;
use crate::snapshot::read_grid_snapshot;
use crate::PlacedCell;

use super::html::write_html;
use super::json::write_json;

pub fn publish_json(output: &Path) -> anyhow::Result<TableExport> {
    let doc = read_grid_snapshot()?;
    write_json(output, &doc)?;
    Ok(doc)
}

pub fn publish_html(output: &Path) -> anyhow::Result<()> {
    let doc = read_grid_snapshot()?;
    let placed = rows_to_placed(&doc);
    write_html(output, &placed, doc.column_count)
}

fn rows_to_placed(doc: &TableExport) -> Vec<Vec<PlacedCell>> {
    doc.rows
        .iter()
        .map(|row| {
            row.cells
                .iter()
                .map(|c| PlacedCell {
                    text: c.text.clone(),
                    col: c.col,
                    colspan: c.colspan,
                    rowspan: c.rowspan,
                })
                .collect()
        })
        .collect()
}
