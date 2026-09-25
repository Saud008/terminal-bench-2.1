use std::collections::HashSet;

use crate::PlacedCell;
use crate::RawCell;

/// Place cells on a logical grid with colspan and rowspan occupancy.
pub fn place_grid(rows: &[Vec<RawCell>]) -> (Vec<Vec<PlacedCell>>, usize) {
    let mut placed_rows: Vec<Vec<PlacedCell>> = Vec::new();
    let mut max_cols = 0usize;

    for row in rows {
        let mut col = 0usize;
        let mut placed: Vec<PlacedCell> = Vec::new();
        for cell in row {
            placed.push(PlacedCell {
                text: cell.text.clone(),
                col,
                colspan: cell.colspan,
                rowspan: cell.rowspan,
            });
            col += cell.colspan;
        }
        max_cols = max_cols.max(col);
        placed_rows.push(placed);
    }

    (placed_rows, max_cols)
}

pub fn occupied_key(row: usize, col: usize) -> (usize, usize) {
    (row, col)
}

pub fn mark_occupied(_seen: &mut HashSet<(usize, usize)>, _row: usize, _col: usize, _colspan: usize, _rowspan: usize) {
}
