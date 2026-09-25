use chrono::{Duration, NaiveDate};

pub fn extended_expiry(base: &str, cold_chain_days: u32, stability_bonus_days: u32) -> Result<String, String> {
    let parsed = NaiveDate::parse_from_str(base, "%Y-%m-%d").map_err(|e| e.to_string())?;
    let total = i64::from(cold_chain_days) + i64::from(stability_bonus_days);
    let out = parsed + Duration::days(total);
    Ok(out.format("%Y-%m-%d").to_string())
}
