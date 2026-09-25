use crate::types::MsgRow;
use std::collections::BTreeMap;

pub fn assert_monotonic(rows: &[MsgRow]) -> Result<(), String> {
    let mut last: BTreeMap<String, u64> = BTreeMap::new();
    for row in rows {
        if let Some(prev) = last.get(&row.topic) {
            if row.header_stamp_ns <= *prev {
                return Err(format!("non-monotonic stamp on {}", row.topic));
            }
        }
        last.insert(row.topic.clone(), row.header_stamp_ns);
    }
    Ok(())
}
