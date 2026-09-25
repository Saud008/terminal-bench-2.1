use crate::types::OverlapRow;

pub fn sort_rows(rows: &mut [OverlapRow]) {
    rows.sort_by(|a, b| {
        a.country
            .cmp(&b.country)
            .then_with(|| a.asn.cmp(&b.asn))
            .then_with(|| a.cidr.cmp(&b.cidr))
    });
}
