use crate::model::{InventorySlot, Output, OutputPlacement, RecipeBook};

/// Plan output placement with stack_max and slot_limit checks before merge.
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

    let mut placements = Vec::new();
    let mut new_slots_needed = 0u32;

    if output.stackable && item_def.stackable {
        if let Some(existing) = slots.iter().find(|s| s.item == output.item) {
            let merged = existing.qty.saturating_add(total_qty);
            if merged > item_def.stack_max {
                return Err("stack overflow".into());
            }
            placements.push(OutputPlacement {
                item: output.item.clone(),
                qty: total_qty,
                target_slot: Some(existing.slot),
                new_slot: false,
            });
        } else {
            if total_qty > item_def.stack_max {
                return Err("stack overflow".into());
            }
            new_slots_needed = 1;
            placements.push(OutputPlacement {
                item: output.item.clone(),
                qty: total_qty,
                target_slot: None,
                new_slot: true,
            });
        }
    } else {
        new_slots_needed = batch_qty;
        for _ in 0..batch_qty {
            if output.qty > item_def.stack_max {
                return Err("stack overflow".into());
            }
            placements.push(OutputPlacement {
                item: output.item.clone(),
                qty: output.qty,
                target_slot: None,
                new_slot: true,
            });
        }
    }

    let used = slots.len() as u32;
    if used + new_slots_needed > book.slot_limit {
        return Err("inventory full".into());
    }

    Ok(placements)
}
