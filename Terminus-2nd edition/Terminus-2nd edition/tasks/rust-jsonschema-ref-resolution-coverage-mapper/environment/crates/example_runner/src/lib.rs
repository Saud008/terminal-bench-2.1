use combinator_cov::{walk_combinators, ComboCoverage};
use doc_loader::SchemaDoc;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct ExampleRow {
    pub schema_id: String,
    pub instance: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExampleCoverage {
    pub schema_id: String,
    pub example_id: String,
    pub all_of_branches: Vec<String>,
    pub any_of_branches: Vec<String>,
}

pub fn evaluate_examples(docs: &[SchemaDoc], examples: &[ExampleRow]) -> Vec<ExampleCoverage> {
    let mut out = Vec::new();
    for (idx, ex) in examples.iter().enumerate() {
        let Some(doc) = docs.iter().find(|d| d.id == ex.schema_id) else {
            continue;
        };
        let mut cov = ComboCoverage::default();
        walk_combinators(&doc.root, "", &ex.instance, &mut cov);
        out.push(ExampleCoverage {
            schema_id: ex.schema_id.clone(),
            example_id: format!("ex-{idx:03}"),
            all_of_branches: cov.all_of.into_iter().collect(),
            any_of_branches: cov.any_of.into_iter().collect(),
        });
    }
    out.sort_by(|a, b| (a.schema_id.as_str(), a.example_id.as_str()).cmp(&(b.schema_id.as_str(), b.example_id.as_str())));
    out
}
