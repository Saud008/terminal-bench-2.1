use crate::voyage_err::SegmentError;
use crate::maritime_types::AisRow;
use time::format_description::well_known::Rfc3339;
use time::OffsetDateTime;

pub fn parse_jsonl(raw: &str) -> Result<Vec<AisRow>, SegmentError> {
    let mut rows = Vec::new();
    for (lineno, line) in raw.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let v: serde_json::Value =
            serde_json::from_str(line).map_err(|e| SegmentError::Parse(format!("line {}: {e}", lineno + 1)))?;
        let seq = v
            .get("seq")
            .and_then(|x| x.as_u64())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing seq", lineno + 1)))? as u32;
        let mmsi = v
            .get("mmsi")
            .and_then(|x| x.as_u64())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing mmsi", lineno + 1)))?;
        let ts = v
            .get("ts")
            .and_then(|x| x.as_str())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing ts", lineno + 1)))?;
        let lat = v
            .get("lat")
            .and_then(|x| x.as_f64())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing lat", lineno + 1)))?;
        let lon = v
            .get("lon")
            .and_then(|x| x.as_f64())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing lon", lineno + 1)))?;
        let sog = v
            .get("sog")
            .and_then(|x| x.as_f64())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing sog", lineno + 1)))?;
        let draught = v
            .get("draught")
            .and_then(|x| x.as_f64())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing draught", lineno + 1)))?;
        let station = v
            .get("station")
            .and_then(|x| x.as_str())
            .ok_or_else(|| SegmentError::Parse(format!("line {} missing station", lineno + 1)))?
            .to_string();
        let ts_epoch = parse_ts_epoch(ts)?;
        rows.push(AisRow {
            seq,
            mmsi,
            ts_epoch,
            lat,
            lon,
            sog,
            draught,
            station,
        });
    }
    Ok(rows)
}

pub fn parse_ts_epoch(ts: &str) -> Result<i64, SegmentError> {
    let dt = OffsetDateTime::parse(ts, &Rfc3339).map_err(|e| SegmentError::Parse(e.to_string()))?;
    Ok((dt - OffsetDateTime::UNIX_EPOCH).whole_seconds())
}
