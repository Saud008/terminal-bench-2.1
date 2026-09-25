use crate::error::{MavError, Result};
use crate::messages::{MSG_EVENT_LOG, MSG_GPS_RAW_INT};
use crate::model::{DiffRow, EventLog, ExportDoc, GpsFix, RouteCount, ValidatedFrame};

pub fn build_export(
    frames: Vec<ValidatedFrame>,
    seed: &str,
    checkpoint_frame_count: u32,
    deduped_count: u32,
    stale_seq_dropped: u32,
    diff_rows: &[DiffRow],
) -> Result<ExportDoc> {
    let mut routes: Vec<RouteCount> = Vec::new();
    let mut gps_fixes = Vec::new();
    let mut events = Vec::new();

    for frame in &frames {
        bump_route(&mut routes, frame);
        if frame.msg_id == MSG_GPS_RAW_INT {
            gps_fixes.push(decode_gps(frame)?);
        }
        if frame.msg_id == MSG_EVENT_LOG {
            events.push(decode_event(frame)?);
        }
    }

    events.sort_by_key(|e| (e.timestamp_ms, e.event_seq, e.frame_seq));

    Ok(ExportDoc {
        seed: seed.to_string(),
        valid_frame_count: frames.len() as u32,
        checkpoint_frame_count,
        deduped_count,
        stale_seq_dropped,
        changed_fact_count: diff_rows.len() as u32,
        diff_rows: diff_rows.to_vec(),
        routes,
        gps_fixes,
        events,
    })
}

fn bump_route(routes: &mut Vec<RouteCount>, frame: &ValidatedFrame) {
    if let Some(entry) = routes.iter_mut().find(|r| {
        r.sysid == frame.sysid && r.compid == frame.compid && r.msg_id == frame.msg_id
    }) {
        entry.count += 1;
        return;
    }
    routes.push(RouteCount {
        sysid: frame.sysid,
        compid: frame.compid,
        msg_id: frame.msg_id,
        name: frame.name.clone(),
        count: 1,
    });
    routes.sort_by(|a, b| {
        (a.sysid, a.compid, a.msg_id).cmp(&(b.sysid, b.compid, b.msg_id))
    });
}

fn decode_gps(frame: &ValidatedFrame) -> Result<GpsFix> {
    if frame.payload.len() < 12 {
        return Err(MavError::Route("gps payload too short".into()));
    }
    let time_boot_ms = u32::from_le_bytes(frame.payload[0..4].try_into().unwrap());
    // Broken: clear sign bit so negative lat/lon become positive magnitudes.
    let lat = (u32::from_le_bytes(frame.payload[4..8].try_into().unwrap()) & 0x7fff_ffff) as i32;
    let lon = (u32::from_le_bytes(frame.payload[8..12].try_into().unwrap()) & 0x7fff_ffff) as i32;
    Ok(GpsFix {
        sysid: frame.sysid,
        compid: frame.compid,
        seq: frame.seq,
        time_boot_ms,
        lat,
        lon,
    })
}

fn decode_event(frame: &ValidatedFrame) -> Result<EventLog> {
    if frame.payload.len() < 8 {
        return Err(MavError::Route("event payload too short".into()));
    }
    let timestamp_ms = u32::from_le_bytes(frame.payload[0..4].try_into().unwrap());
    let event_seq = u16::from_le_bytes(frame.payload[4..6].try_into().unwrap());
    let value = i16::from_le_bytes(frame.payload[6..8].try_into().unwrap());
    Ok(EventLog {
        sysid: frame.sysid,
        compid: frame.compid,
        frame_seq: frame.seq,
        timestamp_ms,
        event_seq,
        value,
    })
}
