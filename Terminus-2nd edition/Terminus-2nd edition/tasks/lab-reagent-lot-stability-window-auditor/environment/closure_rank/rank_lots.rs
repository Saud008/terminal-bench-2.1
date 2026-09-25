use crate::win_schema::ClosureRow;

pub fn sort_rows(rows: &mut [ClosureRow]) {
    rows.sort_by(|a, b| a.lot_id.cmp(&b.lot_id));
}
