pub fn classify_trigger(code: u8) -> String {
    match code {
        0 => "manual".to_string(),
        1 => "distance".to_string(),
        2 => "time".to_string(),
        _ => "manual".to_string(),
    }
}
