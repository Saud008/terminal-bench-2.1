use std::fs;
use std::path::Path;

use crate::grammar::prec::build_climb_table;
use crate::types::{GrammarInput, GrammarRow, GraphFile};
use crate::staging;

pub fn ingest_directory(dir: &str, graph_path: &str) -> Result<(), String> {
    let entries = fs::read_dir(dir).map_err(|e| e.to_string())?;
    let mut names: Vec<String> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .filter(|n| n.ends_with(".json"))
        .collect();
    names.sort();

    let mut grammars = Vec::new();
    for (idx, name) in names.iter().enumerate() {
        let path = Path::new(dir).join(name);
        let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let input: GrammarInput = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        grammars.push(GrammarRow {
            grammar_id: input.grammar_id.clone(),
            start: input.start.clone(),
            sequence_terminator: input.sequence_terminator.clone(),
            rules: input.rules,
            source: name.clone(),
            ingest_order: (idx + 1) as u32,
        });
    }

    let climb_table = build_climb_table(&grammars);
    let prev_seq = staging::load_graph(graph_path)
        .ok()
        .map(|g| g.ingest_seq)
        .unwrap_or(0);
    let graph = GraphFile {
        ingest_seq: prev_seq + 1,
        grammars,
        climb_table,
    };
    staging::save_graph(graph_path, &graph)
}
