use crate::catalog_schema::AtlasSiteRow;

pub fn sort_rows(rows: &mut [AtlasSiteRow]) {
    rows.sort_by(|a, b| {
        a.holder
            .cmp(&b.holder)
            .then_with(|| a.band_id.cmp(&b.band_id))
            .then_with(|| a.site_id.cmp(&b.site_id))
    });
}
