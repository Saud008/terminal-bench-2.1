use lab_calibration_chain::chain_schema::ReadingRow;

pub fn channel_decisions(readings: &[ReadingRow]) -> Vec<(String, bool, f64)> {
    readings
        .iter()
        .map(|r| {
            let deviation = (r.value - r.nominal).abs();
            let within = r.value <= r.nominal + r.tol_plus && r.value >= r.nominal - r.tol_minus;
            (r.channel.clone(), within, deviation)
        })
        .collect()
}

pub fn oot_count(readings: &[ReadingRow]) -> i32 {
    channel_decisions(readings)
        .iter()
        .filter(|(_, within, _)| !within)
        .count() as i32
}
