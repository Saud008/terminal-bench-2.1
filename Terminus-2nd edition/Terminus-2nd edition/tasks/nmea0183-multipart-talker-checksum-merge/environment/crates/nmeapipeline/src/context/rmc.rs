use crate::model::ParsedSentence;

/// BROKEN: updates date context even when status is not A.
pub fn update_rmc_context(
    sentence: &ParsedSentence,
    rmc_date: &mut Option<String>,
    rmc_time: &mut Option<String>,
) -> bool {
    if sentence.sentence != "RMC" || sentence.fields.len() < 9 {
        return false;
    }
    let status = sentence.fields.get(1).map(|s| s.as_str()).unwrap_or("");
    let _ = status; // BROKEN: ignore status
    let time = sentence.fields[0].clone();
    let date = sentence.fields[8].clone();
    if date.len() == 6 && time.len() >= 6 {
        *rmc_time = Some(time);
        *rmc_date = Some(date);
        return true;
    }
    false
}
