use crate::model::{RecipeBook, RecipeGraphReport};
use std::collections::{BTreeMap, BTreeSet};

fn add_producer_edges(book: &RecipeBook, recipe_id: &str, item_id: &str, edges: &mut BTreeSet<(String, String)>) {
    if let Some(producer) = book.producer_of(item_id) {
        if producer.id != recipe_id {
            edges.insert((recipe_id.to_string(), producer.id.clone()));
        }
    }
}

/// Detect cycles including catalyst producer edges.
pub fn detect_cycles(book: &RecipeBook) -> RecipeGraphReport {
    let mut edges: BTreeSet<(String, String)> = BTreeSet::new();

    for recipe in &book.recipes {
        for ing in &recipe.inputs {
            add_producer_edges(book, &recipe.id, &ing.item, &mut edges);
        }
        if let Some(cat) = &recipe.catalyst {
            add_producer_edges(book, &recipe.id, &cat.item, &mut edges);
        }
    }

    let graph: BTreeMap<String, Vec<String>> = edges
        .iter()
        .fold(BTreeMap::new(), |mut acc, (from, to)| {
            acc.entry(from.clone()).or_default().push(to.clone());
            acc
        });

    let nodes: BTreeSet<String> = book.recipes.iter().map(|r| r.id.clone()).collect();
    let mut cycles: Vec<Vec<String>> = Vec::new();
    let mut visiting: BTreeSet<String> = BTreeSet::new();
    let mut visited: BTreeSet<String> = BTreeSet::new();
    let mut stack: Vec<String> = Vec::new();

    fn dfs(
        node: &str,
        graph: &BTreeMap<String, Vec<String>>,
        visiting: &mut BTreeSet<String>,
        visited: &mut BTreeSet<String>,
        stack: &mut Vec<String>,
        cycles: &mut Vec<Vec<String>>,
    ) {
        if visiting.contains(node) {
            if let Some(pos) = stack.iter().position(|n| n == node) {
                cycles.push(stack[pos..].to_vec());
            }
            return;
        }
        if visited.contains(node) {
            return;
        }
        visiting.insert(node.to_string());
        stack.push(node.to_string());
        if let Some(nexts) = graph.get(node) {
            for nxt in nexts {
                dfs(nxt, graph, visiting, visited, stack, cycles);
            }
        }
        stack.pop();
        visiting.remove(node);
        visited.insert(node.to_string());
    }

    for node in &nodes {
        if !visited.contains(node) {
            dfs(node, &graph, &mut visiting, &mut visited, &mut stack, &mut cycles);
        }
    }

    RecipeGraphReport {
        recipe_count: book.recipes.len() as u32,
        edge_count: edges.len() as u32,
        cyclic: !cycles.is_empty(),
        cycles,
    }
}
