use crate::model::{Recipe, RecipeBook, ResolvedIngredient};

pub fn resolve_inputs(book: &RecipeBook, recipe: &Recipe, batch_qty: u32) -> Vec<ResolvedIngredient> {
    let mut merged: std::collections::BTreeMap<String, u32> = std::collections::BTreeMap::new();
    for ing in &recipe.inputs {
        let scaled = ing.qty.saturating_mul(batch_qty);
        *merged.entry(ing.item.clone()).or_insert(0) += scaled;
    }
    let _ = book;
    merged
        .into_iter()
        .map(|(item, qty)| ResolvedIngredient { item, qty })
        .collect()
}
