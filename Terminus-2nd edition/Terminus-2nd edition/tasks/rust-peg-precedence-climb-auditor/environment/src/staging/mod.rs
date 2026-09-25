use std::fs;
use std::path::Path;

use crate::types::GraphFile;

pub fn load_graph(path: &str) -> Result<GraphFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_graph(path: &str, graph: &GraphFile) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(graph).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn grammar_by_id<'a>(graph: &'a GraphFile, grammar_id: &str) -> Option<&'a crate::types::GrammarRow> {
    graph.grammars.iter().find(|g| g.grammar_id == grammar_id)
}
