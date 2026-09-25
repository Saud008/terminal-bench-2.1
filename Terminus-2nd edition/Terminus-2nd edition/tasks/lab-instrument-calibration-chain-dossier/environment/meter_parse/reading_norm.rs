use crate::chain_schema::ReadingRow;

pub fn normalize_readings(rows: &[ReadingRow]) -> Vec<ReadingRow> {
    rows.to_vec()
}

pub fn channel_count(rows: &[ReadingRow]) -> usize {
    rows.len()
}
