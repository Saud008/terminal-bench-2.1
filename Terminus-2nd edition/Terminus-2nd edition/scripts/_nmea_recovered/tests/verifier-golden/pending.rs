        pending.sort_by_key(|sentence| {
            sentence
                .fields
                .get(1)
                .and_then(|v| v.parse::<u32>().ok())
                .unwrap_or(0)
       