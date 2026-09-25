pub fn attach_utc(rmc_date: Option<&str>, rmc_time: Option<&str>, time_field: &str) -> Option<String> {
    let date = rmc_date?;
    if date.len() != 6 {
        return None;
    }
    let mut day: u32 = date[0..2].parse().ok()?;
    let mut month: u32 = date[2..4].parse().ok()?;
    let mut year: u32 = 2000 + date[4..6].parse::<u32>().ok()?;
    let (hh, mm, ss) = parse_time(time_field)?;
    if let Some(rt) = rmc_time {
        if let Some((rh, _, _)) = parse_time(rt) {
            if hh < rh {
                day += 1;
                let dim = days_in_month(year, month);
                if day > dim {
                    day = 1;
                    month += 1;
                    if month > 12 {
                        month = 1;
                        year += 1;
                    }
                }
            }
        }
    }
    Some(format!("{year:04}-{month:02}-{day:02}T{hh:02}:{mm:02}:{ss:02}Z"))
}

fn parse_time(t: &str) -> Option<(u32, u32, u32)> {
    if t.len() < 6 {
        return None;
    }
    Some((t[0..2].parse().ok()?, t[2..4].parse().ok()?, t[4..6].parse().ok()?))
}

pub fn days_in_month(year: u32, month: u32) -> u32 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) {
                29
            } else {
                28
            }
        }
        _ => 30,
    }
}
