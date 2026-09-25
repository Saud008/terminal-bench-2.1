use query_planner::or_branch::term_weight;
use query_planner::parse::{parse_query, QueryMode};
use xapi_length::norm::length_norm;
use xapi_synonym::expand::effective_wdf;
use xapi_types::index::IndexFile;
use xapi_types::query::{Hit, QueryResult};
use xapi_wdf::collector::wdf_map;

pub fn rare_cf() -> u64 {
    std::env::var("TB3_RARE_CF")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(2)
}

fn idf(n: u64, cf: u64) -> f64 {
    ((n + 1) as f64 / (cf + 1) as f64).ln()
}

pub fn run_query(index: &IndexFile, query: &str) -> Result<QueryResult, String> {
    let parsed = parse_query(query)?;
    let n = index.doc_count();
    let mut hits = Vec::new();
    for doc in &index.documents {
        let wdf = wdf_map(&doc.body);
        let len = length_norm(&doc.body);
        let mut raw = 0.0;
        let is_or = matches!(parsed.mode, QueryMode::Or);
        for term in &parsed.terms {
            let eff = effective_wdf(term, &wdf, &doc.synonyms);
            if matches!(parsed.mode, QueryMode::And) && eff <= 0.0 {
                raw = 0.0;
                break;
            }
            let cf = *index.cf.get(term).unwrap_or(&0);
            let tw = term_weight(eff, idf(n, cf), cf, rare_cf(), is_or);
            if matches!(parsed.mode, QueryMode::Or) {
                raw += tw;
            } else {
                raw += tw;
            }
        }
        if raw > 0.0 {
            hits.push(Hit {
                docid: doc.docid.clone(),
                score: raw * len,
            });
        }
    }
    hits.sort_by(|a, b| {
        b.score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| a.docid.cmp(&b.docid))
    });
    Ok(QueryResult {
        hits,
        mode: format!("{:?}", parsed.mode),
        query: query.to_string(),
    })
}
