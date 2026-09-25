use crate::maritime_types::AisRow;

pub fn stable_track_order(points: &mut [AisRow]) {
    points.sort_by(|a, b| {
        a.mmsi
            .cmp(&b.mmsi)
            .then(a.ts_epoch.cmp(&b.ts_epoch))
            .then(a.seq.cmp(&b.seq))
    });
}
