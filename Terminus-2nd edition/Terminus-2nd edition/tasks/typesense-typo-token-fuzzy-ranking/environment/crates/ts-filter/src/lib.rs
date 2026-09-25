pub mod brand_filter;

use ts_types::document::Document;

pub fn apply_brand_filter(docs: &[Document], brand: Option<&str>) -> Vec<Document> {
    match brand {
        None => docs.to_vec(),
        Some(b) => docs
            .iter()
            .filter(|d| brand_filter::brand_matches(d, b))
            .cloned()
            .collect(),
    }
}
