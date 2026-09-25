use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(untagged)]
pub enum DimSpec {
    Static(i64),
    Symbol(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TensorPort {
    pub name: String,
    #[serde(default)]
    pub shape: Vec<DimSpec>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default_shape: Option<Vec<DimSpec>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphNode {
    pub id: String,
    pub op: String,
    pub inputs: Vec<String>,
    pub outputs: Vec<String>,
    #[serde(default)]
    pub attrs: serde_json::Map<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValueInfo {
    pub name: String,
    #[serde(default)]
    pub shape: Option<Vec<DimSpec>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphDoc {
    pub graph_id: String,
    #[serde(default)]
    pub symbol_links: Vec<[String; 2]>,
    pub inputs: Vec<TensorPort>,
    #[serde(default)]
    pub initializers: Vec<TensorPort>,
    pub nodes: Vec<GraphNode>,
    #[serde(default)]
    pub value_infos: Vec<ValueInfo>,
}

pub fn read_graph_dir(dir: &std::path::Path) -> Result<Vec<GraphDoc>, String> {
    let mut docs = Vec::new();
    let mut paths: Vec<_> = std::fs::read_dir(dir)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
        .collect();
    paths.sort();
    for path in paths {
        let raw = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let doc: GraphDoc = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        docs.push(doc);
    }
    Ok(docs)
}

pub fn dim_key(d: &DimSpec) -> String {
    match d {
        DimSpec::Static(v) => format!("s:{v}"),
        DimSpec::Symbol(s) => format!("y:{s}"),
    }
}
