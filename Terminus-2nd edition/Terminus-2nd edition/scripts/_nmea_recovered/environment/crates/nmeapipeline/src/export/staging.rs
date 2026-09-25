    let snapshot: MergeSnapshot = serde_json::from_str(&text).map_err(|e| e.to_string())?;
    crate::export::validate::validate_snapshot(&snapshot)?;
    crate::export::writer::verify_digest(&snapsho