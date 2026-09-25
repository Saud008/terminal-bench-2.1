pub fn wx_unit_bytes(dtype: &str) -> Option<u64> {
    match dtype {
        "F32" | "I32" => Some(4),
        "F16" => Some(2),
        "BF16" => Some(4),
        "I64" => Some(8),
        "U8" => Some(1),
        _ => None,
    }
}

pub fn wx_payload_units(dtype: &str, shape: &[u64]) -> Option<u64> {
    let esz = wx_unit_bytes(dtype)?;
    let mut count = 1u64;
    for d in shape {
        count = count.saturating_mul(*d);
    }
    Some(count.saturating_mul(esz))
}
