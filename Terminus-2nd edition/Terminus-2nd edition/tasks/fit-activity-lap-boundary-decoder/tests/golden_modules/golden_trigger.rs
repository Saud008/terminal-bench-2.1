pub fn classify_trigger(code: u8) -> String {
    match code {
        0 => "manual".to_string(),
        1 => "time".to_string(),
        2 => "distance".to_string(),
        3 => "session-end".to_string(),
        _ => "unknown".to_string(),
    }
}
