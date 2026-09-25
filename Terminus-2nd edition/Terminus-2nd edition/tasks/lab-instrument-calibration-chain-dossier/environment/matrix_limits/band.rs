use crate::chain_schema::ReadingRow;

pub fn channel_decisions(readings: &[ReadingRow]) -> Vec<(String, bool, f64)> {
    readings
        .iter()
        .map(|r| {
            let band = r.tol_plus.max(r.tol_minus);
            let deviation = (r.value - r.nominal).abs();
            let within = deviation <= band;
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
