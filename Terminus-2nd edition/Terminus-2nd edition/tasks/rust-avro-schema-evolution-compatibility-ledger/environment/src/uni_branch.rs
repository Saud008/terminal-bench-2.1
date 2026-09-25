use crate::avsc_parse::union_branches;
use serde_json::Value;

pub fn union_compatible(writer: &Value, reader: &Value) -> bool {
    match (union_branches(writer), union_branches(reader)) {
        (Some(w), Some(r)) => w == r,
        (None, None) => true,
        _ => false,
    }
}
