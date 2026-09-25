use std::collections::BTreeMap;

use query_planner::parse::parse_query;
use ts_facet::counter::facet_brand_counts;
use ts_filter::apply_brand_filter;
use ts_fuzzy::typo_expand::expand_token;
use ts_ranker::rank_documents;
use ts_types::index::IndexFile;
use ts_types::search::SearchResult;

pub fn run_search(index: &IndexFile, query: &str, brand_filter: Option<&str>) -> Result<SearchResult, String> {
    let query_tokens = parse_query(query)?;
    let filtered = apply_brand_filter(&index.documents, brand_filter);
    let filtered_vocab = filtered
        .iter()
        .flat_map(|d| ts_tokenize::token_dedupe::index_terms(&d.searchable_text()))
        .collect::<Vec<_>>();
    let expanded = query_tokens
        .iter()
        .map(|t| expand_token(t, &filtered_vocab))
        .collect::<Vec<_>>();
    let hits = rank_documents(&filtered, &query_tokens, &expanded, &filtered_vocab);
    let facets = BTreeMap::from([(
        "brand".to_string(),
        facet_brand_counts(&index.documents, &filtered),
    )]);
    Ok(SearchResult {
        hits,
        facets,
        query: query.to_string(),
        filter_brand: brand_filter.map(|s| s.to_string()),
    })
}
