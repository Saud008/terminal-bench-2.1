use std::collections::HashSet;

use crate::PlacedCell;
use crate::RawCell;

pub fn place_grid(rows: &[Vec<RawCell>]) -> (Vec<Vec<PlacedCell>>, usize) {
    let mut occupied: HashSet<(usize, usize)> = HashSet::new();
    let mut placed_rows: Vec<Vec<PlacedCell>> = Vec::new();
    let mut max_width = 0usize;

    for (row_index, row) in rows.iter().enumerate() {
        let mut col = 0usize;
        let mut placed: Vec<PlacedCell> = Vec::new();
        for cell in row {
            while occupied.contains(&(row_index, col)) {
                col += 1;
            }
            placed.push(PlacedCell {
                text: cell.text.clone(),
                col,
                colspan: cell.colspan,
                rowspan: cell.rowspan,
            });
            for dr in 0..cell.rowspan {
                for dc in 0..cell.colspan {
                    occupied.insert((row_index + dr, col + dc));
                }
            }
            max_width = max_width.max(col + cell.colspan);
            col += cell.colspan;
        }
        placed_rows.push(placed);
    }

    (placed_rows, max_width)
}
