use crate::model::{InventorySlot, Output, OutputPlacement, RecipeBook};

pub fn plan_output_placement(
    book: &RecipeBook,
    slots: &[InventorySlot],
    output: &Output,
    batch_qty: u32,
) -> Result<Vec<OutputPlacement>, String> {
    let total_qty = output.qty.saturating_mul(batch_qty);
    let item_def = book
        .item_def(&output.item)
        .ok_or_else(|| format!("unknown item {}", output.item))?;

    let mut working: Vec<InventorySlot> = slots.to_vec();
    let mut placements = Vec::new();

    if output.stackable && item_def.stackable {
        if let Some(idx) = working.iter().position(|s| s.item == output.item) {
            working[idx].qty = working[idx].qty.saturating_add(total_qty);
            placements.push(OutputPlacement {
                item: output.item.clone(),
                qty: total_qty,
                target_slot: Some(working[idx].slot),
                new_slot: false,
            });
        } else {
            placements.push(OutputPlacement {
                item: output.item.clone(),
                qty: total_qty,
                target_slot: None,
                new_slot: true,
            });
        }
    } else {
        for _ in 0..batch_qty {
            placements.push(OutputPlacement {
                item: output.item.clone(),
                qty: output.qty,
                target_slot: None,
                new_slot: true,
            });
        }
    }

    let used_slots = working.len() as u32;
    let new_slots = placements.iter().filter(|p| p.new_slot).count() as u32;
    if used_slots + new_slots > book.slot_limit {
        return Err("inventory full".into());
    }

    Ok(placements)
}
