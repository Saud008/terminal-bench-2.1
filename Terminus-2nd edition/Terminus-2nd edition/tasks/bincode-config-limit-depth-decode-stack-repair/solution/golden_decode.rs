use crate::error::DecodeError;
use crate::limit::LimitTracker;
use crate::report::DecodeReport;
use crate::visitor::Visitor;

pub const HEADER: &[u8] = b"BLIM\x01";

pub fn decode_payload(data: &[u8], max_depth: u32, max_bytes: u64) -> DecodeReport {
    if data.len() < HEADER.len() || &data[..HEADER.len()] != HEADER {
        return DecodeReport::error(DecodeError::InvalidTag(0xff), 0, max_bytes);
    }
    let body = &data[HEADER.len()..];
    let mut limits = LimitTracker::new(max_depth, max_bytes);
    let mut visitor = Visitor::new(body, &mut limits);
    match visitor.decode_value() {
        Ok(value) => DecodeReport::ok(value, limits.bytes_consumed(max_bytes)),
        Err(err) => DecodeReport::error(err, limits.bytes_consumed(max_bytes), max_bytes),
    }
}
