use crate::model::{Recipe, RecipeBook, ResolvedIngredient};

/// Resolve recipe inputs: substitute map before batch multiply.
pub fn resolve_inputs(book: &RecipeBook, recipe: &Recipe, batch_qty: u32) -> Vec<ResolvedIngredient> {
    let mut merged: std::collections::BTreeMap<String, u32> = std::collections::BTreeMap::new();
    for ing in &recipe.inputs {
        let effective = book
            .substitutes
            .get(&ing.item)
            .cloned()
            .unwrap_or_else(|| ing.item.clone());
        let required = ing.qty.saturating_mul(batch_qty);
        *merged.entry(effective).or_insert(0) += required;
    }
    merged
        .into_iter()
        .map(|(item, qty)| ResolvedIngredient { item, qty })
        .collect()
}
