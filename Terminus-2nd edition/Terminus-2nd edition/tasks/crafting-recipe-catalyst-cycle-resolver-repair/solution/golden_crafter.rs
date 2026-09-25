use crate::model::{CraftPreview, InventorySlot, RecipeBook};
use crate::stack::plan_output_placement;
use crate::substitute::resolve_inputs;

pub fn preview_craft(
    book: &RecipeBook,
    slots: &[InventorySlot],
    recipe_id: &str,
    batch_qty: u32,
) -> CraftPreview {
    let Some(recipe) = book.recipe(recipe_id) else {
        return CraftPreview {
            recipe_id: recipe_id.to_string(),
            batch_qty,
            inputs: vec![],
            catalyst: None,
            outputs: vec![],
            ok: false,
            reason: Some("unknown recipe".into()),
        };
    };

    let inputs = resolve_inputs(book, recipe, batch_qty);
    let catalyst = recipe.catalyst.as_ref().map(|c| {
        let qty = if c.consumed {
            c.qty.saturating_mul(batch_qty)
        } else {
            c.qty
        };
        crate::model::ResolvedIngredient {
            item: c.item.clone(),
            qty,
        }
    });

    let outputs = match plan_output_placement(book, slots, &recipe.output, batch_qty) {
        Ok(p) => p,
        Err(reason) => {
            return CraftPreview {
                recipe_id: recipe.id.clone(),
                batch_qty,
                inputs,
                catalyst: catalyst.clone(),
                outputs: vec![],
                ok: false,
                reason: Some(reason),
            };
        }
    };

    if !has_materials(slots, &inputs) {
        return CraftPreview {
            recipe_id: recipe.id.clone(),
            batch_qty,
            inputs,
            catalyst: catalyst.clone(),
            outputs,
            ok: false,
            reason: Some("insufficient materials".into()),
        };
    }

    if let Some(cat) = &catalyst {
        if !has_item_qty(slots, &cat.item, cat.qty) {
            return CraftPreview {
                recipe_id: recipe.id.clone(),
                batch_qty,
                inputs,
                catalyst: catalyst.clone(),
                outputs,
                ok: false,
                reason: Some("missing catalyst".into()),
            };
        }
    }

    CraftPreview {
        recipe_id: recipe.id.clone(),
        batch_qty,
        inputs,
        catalyst,
        outputs,
        ok: true,
        reason: None,
    }
}

pub fn apply_craft(
    book: &RecipeBook,
    slots: &mut Vec<InventorySlot>,
    recipe_id: &str,
    batch_qty: u32,
) -> Result<CraftPreview, String> {
    let preview = preview_craft(book, slots, recipe_id, batch_qty);
    if !preview.ok {
        return Err(preview.reason.unwrap_or_else(|| "craft rejected".into()));
    }

    let recipe = book.recipe(recipe_id).ok_or_else(|| "unknown recipe".to_string())?;

    for ing in &preview.inputs {
        deduct_item(slots, &ing.item, ing.qty)?;
    }

    if let Some(cat) = &preview.catalyst {
        if recipe
            .catalyst
            .as_ref()
            .map(|c| c.consumed)
            .unwrap_or(false)
        {
            deduct_item(slots, &cat.item, cat.qty)?;
        }
    }

    for placement in &preview.outputs {
        if placement.new_slot {
            let next = next_slot(slots);
            slots.push(InventorySlot {
                slot: next,
                item: placement.item.clone(),
                qty: placement.qty,
            });
        } else if let Some(target) = placement.target_slot {
            if let Some(slot) = slots.iter_mut().find(|s| s.slot == target) {
                slot.qty = slot.qty.saturating_add(placement.qty);
            }
        }
    }

    Ok(preview)
}

pub fn deduct_item_public(slots: &mut Vec<InventorySlot>, item: &str, qty: u32) -> Result<(), String> {
    deduct_item(slots, item, qty)
}

fn has_materials(slots: &[InventorySlot], needs: &[crate::model::ResolvedIngredient]) -> bool {
    needs
        .iter()
        .all(|n| has_item_qty(slots, &n.item, n.qty))
}

fn has_item_qty(slots: &[InventorySlot], item: &str, qty: u32) -> bool {
    slots
        .iter()
        .filter(|s| s.item == item)
        .map(|s| s.qty)
        .sum::<u32>()
        >= qty
}

fn deduct_item(slots: &mut Vec<InventorySlot>, item: &str, qty: u32) -> Result<(), String> {
    let mut remaining = qty;
    for slot in slots.iter_mut().filter(|s| s.item == item) {
        if remaining == 0 {
            break;
        }
        let take = remaining.min(slot.qty);
        slot.qty -= take;
        remaining -= take;
    }
    slots.retain(|s| s.qty > 0);
    if remaining > 0 {
        return Err("deduction failed".into());
    }
    Ok(())
}

fn next_slot(slots: &[InventorySlot]) -> u32 {
    slots.iter().map(|s| s.slot).max().unwrap_or(0) + 1
}
