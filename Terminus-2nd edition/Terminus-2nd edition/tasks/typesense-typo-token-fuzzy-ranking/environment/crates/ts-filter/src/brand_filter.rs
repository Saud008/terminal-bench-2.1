use ts_types::document::Document;

pub fn brand_matches(doc: &Document, brand: &str) -> bool {
    doc.brand.eq_ignore_ascii_case(brand)
}
