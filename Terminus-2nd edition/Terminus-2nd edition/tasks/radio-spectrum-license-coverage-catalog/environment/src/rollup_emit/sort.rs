use crate::catalog_schema::AtlasSiteRow;

pub fn sort_rows(rows: &mut [AtlasSiteRow]) {
    rows.sort_by(|a, b| a.site_id.cmp(&b.site_id));
}
