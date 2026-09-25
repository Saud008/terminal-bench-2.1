    crate::export::validate::validate_snapshot(&snapshot)?;
    crate::export::writer::verify_digest(&snapshot)?;