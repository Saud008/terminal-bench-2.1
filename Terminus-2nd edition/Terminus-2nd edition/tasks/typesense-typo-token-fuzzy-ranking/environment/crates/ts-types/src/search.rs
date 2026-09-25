use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SearchHit {
    pub docid: String,
    pub score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SearchResult {
    pub hits: Vec<SearchHit>,
    pub facets: BTreeMap<String, BTreeMap<String, u64>>,
    pub query: String,
    pub filter_brand: Option<String>,
}
